# reducer.py

from operator import itemgetter
import sys
import nltk

FILENAME_IDX = 0
SENTENCE_INDEX_IDX = 1
SENTENCE_IDK = 2

#sentences = []
# Build a list of tuples of the format: <filename>\t<sentence index>\t<sentence>
for line in sys.stdin:
    line = line.strip()
    if len(line) > 0:
        try:
            filename, chunk_index, sentences = line.strip().split('\t',2)
            for sentence in sentences.split('\\'):
                print('{}\t{}'.format(filename, sentence))
            # Convert sentence index to int for sorting
            #sentences.append((filename, int(sentence_index), sentence))
        except Exception as e:
            continue

# Used to check if we have multiple files on the partition
"""
files = set([item[FILENAME_IDX] for item in sentences])

# Sort based on sentence index
sentences = sorted(sentences, key=itemgetter(SENTENCE_INDEX_IDX))

# Output sentence to partition file, one input file at a time
for f in files:
    for sentence in sentences:
        #tokens = nltk.word_tokenize(str(sentence[SENTENCE_IDK]))
        #tagged = nltk.pos_tag(tokens)
        if sentence[FILENAME_IDX] == f:
            # Output in the format <filename>\t<sentence>
            #print('{}\t{}\t{}'.format(sentence[FILENAME_IDX], sentence[SENTENCE_IDK],tagged))
            print('{}\t{}'.format(sentence[FILENAME_IDX], sentence[SENTENCE_IDK]))
"""