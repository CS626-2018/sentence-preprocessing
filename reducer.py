# reducer.py
# Ryan Zembrodt, Thilina Perera

import sys
import zipimport
importer = zipimport.zipimporter('nltk.mod')
nltk = importer.load_module('nltk')
from nltk.sentiment.vader import SentimentIntensityAnalyzer 

FILENAME_IDX = 0
SENTENCE_INDEX_IDX = 1
SENTENCE_IDK = 2

# Sentiment analyzer
sid = SentimentIntensityAnalyzer()

# Build a list of tuples of the format: <filename>\t<sentence index>\t<sentence>
for line in sys.stdin:
    line = line.strip()
    if len(line) > 0:
        try:
            # Gather filename, chunk index, and senteces from mapper
            filename, chunk_index, sentences = line.strip().split('\t',2)
            # Split the sentences on backslashes
            for sentence in sentences.split('\\'):
                # Extract features from each sentence
                tokens = nltk.word_tokenize(sentence)
                tagged = nltk.pos_tag(tokens)
                ss = sid.polarity_scores(sentence)
                polarities = []
                for k in ss:
                    polarities.append('{},{}'.format(k, ss[k]))
                #print('{}\t{}\t{}'.format(filename, chunk_index, sentence))
                print('{}\t{}\t{}\t{}\t{}'.format(
                    filename, chunk_index, sentence, tagged, polarities))
        except Exception as e:
            print('FAILURE with line [{}], exception: {}'.format(line, repr(e)))
            continue

"""import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer 
  
hotel_rev = ["I like going to the cinema.", "I don't like going to the cinema.", "car is green"]
  
sid = SentimentIntensityAnalyzer()
for sentence in hotel_rev:
     print(sentence)
     ss = sid.polarity_scores(sentence)
     for k in ss:
         print('{0}: {1}, '.format(k, ss[k]), end='')
     print()


# neg: Negative
# neu: Neutral
# pos: Positive
# compound: Compound (i.e. aggregated score)

"""