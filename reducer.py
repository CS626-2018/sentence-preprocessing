# reducer.py

import operator
import sys

for line in sys.stdin:
    line = line.strip()
    if len(line) > 0:
        try:
            filename, sentence_index, sentence = line.strip().split('\t',2)
            print('{}\t{}\t{}'.format(filename, sentence_index, sentence))
        except:
            print('REDUCER FAIL SPLIT: [{}]'.format(line))
