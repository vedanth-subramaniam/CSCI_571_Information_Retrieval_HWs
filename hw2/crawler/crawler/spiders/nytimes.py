import scrapy
import os
import re
import csv
import random    
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NYTSpider(scrapy.Spider):
    name = "nytimes"

    # Custom settings for crawling
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CLOSESPIDER_PAGECOUNT': 10000,
        'DEPTH_LIMIT': 16,
        'DOWNLOAD_DELAY': 2,  
        'COOKIES_ENABLED': False,  
        'RETRY_TIMES': 3,  
        'HTTPERROR_ALLOW_ALL': True,
    }

    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
        'Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/537.36',
    ]

    def __init__(self, *args, **kwargs):
        super(NYTSpider, self).__init__(*args, **kwargs)
        self.allowed_domains = ["nytimes.com"]
        self.visited_urls = set()
        self.setup_output_files()
        
    def start_requests(self):
        url = 'https://www.nytimes.com'
        headers = {'User-Agent': random.choice(self.USER_AGENTS)}
        yield scrapy.Request(url, headers=headers, callback=self.parse, errback=self.errback_handler)
        
    def setup_output_files(self):
        self.create_csv("fetch_nytimes.csv", ["URL", "Status"], overwrite=True)
        self.create_csv("visit_nytimes.csv", ["URL", "Size (KB)", "# Outlinks", "Content-Type"], overwrite=True)
        self.create_csv("urls_nytimes.csv", ["URL", "Indicator"], overwrite=True)
        
    def errback_handler(self, failure):
        """Handles request failures and logs them"""
        url = failure.request.url
        status = failure.request.status
        self.logger.info('Some request has failed')
        self.logger.error(f"Request failed: {url}, Error: {failure.value}")
        self.write_to_csv("fetch_nytimes.csv", [url, status])
            
    def create_csv(self, filename, headers, overwrite=True):
        """Creates CSV files, overwriting existing ones if specified"""
        mode = 'w' if overwrite or not os.path.exists(filename) else 'a'
        with open(filename, mode=mode, newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if mode == 'w':
                writer.writerow(headers)

    def parse(self, response):
        url = response.url
        status = response.status
        self.write_to_csv("fetch_nytimes.csv", [url, status])

        # Handle Redirects (301/302)
        if response.request.meta.get('redirect_urls'):
            original_url = response.request.meta.get('redirect_urls')[0]
            self.logger.info(f"Redirect detected: {original_url} → {url}")
        
        # Skip processing if already visited or error status
        if url in self.visited_urls or status >= 400:
            self.logger.info(f"Skipping {url} (status: {status})")
            return

        self.visited_urls.add(url)

        content_type = response.headers.get('Content-Type', b'').decode('utf-8', errors='ignore').split(';')[0]
        page_size = len(response.body) / 1024  

        try:
            outlinks = response.css('a::attr(href)').getall()
            outlinks = [response.urljoin(link) for link in outlinks if self.is_valid_url(link)]
        except Exception as e:
            self.logger.error(f"Error extracting links from {url}: {e}")
            outlinks = []

        self.write_to_csv("visit_nytimes.csv", [url, round(page_size, 2), len(outlinks), content_type])

        for link in outlinks:
            parsed_link = urlparse(link)
            domain = parsed_link.netloc
            
            if domain == "nytimes.com" or domain == "www.nytimes.com":
                self.write_to_csv("urls_nytimes.csv", [link, "OK"])
                if link not in self.visited_urls:
                    headers = {'User-Agent': random.choice(self.USER_AGENTS)}
                    yield response.follow(link, headers=headers, callback=self.parse, errback=self.errback_handler)
            else:
                self.write_to_csv("urls_nytimes.csv", [link, "N_OK"])

    def write_to_csv(self, filename, row):
        """Appends data to CSV files"""
        try:
            with open(filename, mode='a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row)
        except Exception as e:
            self.logger.error(f"Error writing to {filename}: {e}")


    def is_valid_url(self, url):
        """Validates URLs to only visit HTML, DOC, PDF, and image formats"""
        if not url or url in self.visited_urls:
            return False
        if url.startswith(("javascript:", "mailto:", "tel:", "#")):
            return False
        
        parsed = urlparse(url)
        
        # Ensure the URL has a valid domain (excluding fragments)
        if not parsed.netloc or parsed.fragment:
            return False

        # Allowed file extensions (case-insensitive)
        allowed_extensions = re.compile(r".*\.(html?|pdf|docx?|jpe?g|png|gif|bmp|tiff?|webp)$", re.IGNORECASE)

        # Check if the URL has a valid file extension OR no extension (assuming it's an HTML page)
        if allowed_extensions.match(parsed.path) or not parsed.path.split('.')[-1]:
            return True

        return False

