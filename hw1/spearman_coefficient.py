import json
import numpy as np
import pandas as pd
from scipy.stats import rankdata, spearmanr


def spearman_coeff(indices1, indices2, n):
    diff = sum([abs(a - b) ** 2 for a, b in zip(indices1, indices2)])
    value = 1 - ((6 * diff) / (n * (n ** 2 - 1)))
    return value


def hits(data1, data2):
    results = pd.DataFrame(columns=['Number of Overlapping Results', 'Percent Overlap', 'Spearman Coefficient'], index=pd.Index([], name='Queries'))
    queries = data1.keys()
    
    for query in queries:

        arr1 = np.array(data1[query])
        arr2 = np.array(data2[query])

        common_elements = np.intersect1d(arr1, arr2)

        indices1 = np.array(
            [np.where(arr1 == elem)[0][0] + 1 for elem in common_elements])
        indices2 = np.array(
            [np.where(arr2 == elem)[0][0] + 1 for elem in common_elements])

        overlap = len(common_elements)
        overlap_per = overlap / len(arr1) * 100
        
        if common_elements.size > 1:
            spearman_coeff_val = spearman_coeff(indices1, indices2, len(common_elements))
        elif common_elements.size == 1 and indices1 == indices2:
            spearman_coeff_val = 1
        else:
            spearman_coeff_val = 0
           
        results.loc[query] = [overlap, f'{overlap_per}%', spearman_coeff_val]

    return results


def main():

    with open('hw1/google_results_3.json', 'r') as file1:
        data1 = json.load(file1)
    with open('hw1/bing_results_3.json', 'r') as file2:
        data2 = json.load(file2)

    results = hits(data1, data2)
    results.to_csv('spearman_coefficient.csv')
    
if __name__ == '__main__':
    main()
