# evaluation.py
import getopt
import os
import re
import sys
from nltk.translate.bleu_score import sentence_bleu

HELP_MSG = '\n'.join([
    'Usage:',
    'python3 evaluation.py [-h, --help] [--reference <reference_dir>] [--candidate <candidate_dir>]',
    '\tAll command line arguments are optional, and any combination (beides -h) can be used',
    '\t-h, --help: Provides help on command line parameters',
    '\t--reference <reference_dir>: specify the directory to get reference sentences from',
    '\t--candidate <candidate_dir>: specify the directory to get candidate sentences from'])

# How many sentences to evaluate from each file
EVAL_LIMIT = 5

# Calculates the BLEU score
def calculate_bleu(candidate, reference, n_gram=2):
    # looks at ration of n-grams between 2 texts
    # Break candidate/reference into the format below
    candidate = candidate.split()
    reference = reference.split()
    return sentence_bleu(reference, candidate)

def main(argv):
    try:
        opts, _ = getopt.getopt(argv, 'h', ['reference=', 'candidate=', 'help'])
    except getopt.GetoptError as e:
        print(e)
        print(HELP_MSG)
        exit(1)    

    reference_dir = None
    candidate_dir = None

    for opt, val in opts:
        if opt in ('-h', '--help'):
            print(HELP_MSG)
            exit(0)
        elif opt == '--reference':
            reference_dir = val
        elif opt == '--candidate':
            candidate_dir = val
    
    if reference_dir is None or candidate_dir is None:
        print('Please specify both the reference (--reference) and candidate (--candidate) directories.')
        print(HELP_MSG)
        exit(1)
    
    if reference_dir[-1] not in ('/', '\\'):
        reference_dir += '/'

    # Open candidate files:
    for candidate_file in os.listdir():
        if os.path.isfile(candidate_file) and re.search('part', candidate_file):
            with open(candidate_file, 'r') as f:
                candidate_count = 0
                curr_file = None
                sentences_to_eval = []
                for line in f.readlines():
                    line = line.strip()
                    filename, sentence = line.split('\t', 2)
                    if curr_file is None or candidate_count < EVAL_LIMIT:
                        curr_file = filename
                        candidate_count += 1
                        sentences_to_eval.append(sentence)
                    elif curr_file != sentence:
                        # Calculate bleu score of current sentences
                        # Open the reference file
                        with open(reference_dir + curr_file, 'r') as f_ref:
                            reference_count = 0
                            avg_bleu_score = 0.0
                            for i, ref_line in enumerate(f_ref.readlines()):
                                if reference_count < EVAL_LIMIT:
                                    avg_bleu_score += calculate_bleu(sentences_to_eval[i], ref_line.strip())
                                else:
                                    break
                            avg_bleu_score /= EVAL_LIMIT
                            print('Average bleu score for file [{}]: {:.4f}'.format(curr_file, avg_bleu_score))
                        # Continue to next file
                        curr_file = filename
                        candidate_count = 1
                        sentences_to_eval = [sentence]
                    else:
                        # Continue to next file
                        continue

if __name__ == '__main__':
    main(sys.argv[1:])