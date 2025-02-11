from bs4 import BeautifulSoup
from time import sleep
import requests
from random import randint
from html.parser import HTMLParser
import json


USER_AGENT = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

class SearchEngine:
    @staticmethod
    def search(query, sleep_time=True):
        if sleep_time:
            sleep(randint(10, 20))
        
        temp_url = '+'.join(query.split())
        url = 'http://www.bing.com/search?q=' + temp_url + '&count=30'
        print(url)
        soup = BeautifulSoup(requests.get(url, headers=USER_AGENT).text, "html.parser")
        new_results = SearchEngine.scrape_search_result(soup)
        return new_results

    @staticmethod
    def scrape_search_result(soup):
        results = []
        
        raw_results = soup.find_all('li', {'class': 'b_algo'})
        
        for result in raw_results:
            link = result.find('a', href=True)
            if link:
                href = link['href']
                if href.startswith("http") and href not in results:
                    results.append(href)
                if len(results) >= 10:
                    break
                
        return results

if __name__ == "__main__":
    
    queryFile = open('queries.txt', 'r')
    output_dict = {}
    for query in queryFile:
        results = SearchEngine.search(query)
        output_dict[query.strip()] = results

    with open('result.json', 'w') as fp:
        json.dump(output_dict, fp)
        