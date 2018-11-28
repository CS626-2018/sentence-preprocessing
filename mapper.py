# mapper.py

#import nltk
#import nltk.data
#from nltk.corpus import stopwords
#from nltk.stem.porter import PorterStemmer
import re
import sys
from unidecode import unidecode
import zipimport
importer = zipimport.zipimporter('nltk.mod')
nltk = importer.load_module('nltk')
try:
    from nltk.corpus import stopwords
except Exception as e:
    print('stopwords import failure: [{}]'.format(repr(e)))
    exit()
from nltk import word_tokenize
nltk.data.path+=["."]
try:
    stops = set(stopwords.words('english'))
except Exception as e:
    print('stopwords failure: [{}]'.format(repr(e)))
    exit()

SENTENCE_ENDINGS = ['.', '!', '?', '"']
ABBREVIATIONS = ['mr.', 'mrs.', 'ms.', 'jr.', 'sr.', 'dr.']

CONTRACTION_PAIRS = [
    ('\'ll', ' *ll'),
    ('\'re', ' *re'),
    ('\'s', ' *s'),
    ('\'d', ' *d'),
    ('\'m', ' *m'),
    ('\'ve', ' *ve'),
    ('n\'t', ' not'),
    ('s\'', 's *')
]

# Sentence parsing methods
# Removes unneeded punctuation in the data:
# mr. -> mr, etc
# hyphens between words, ex: A -- B -> A B
# commas, double quotes, hyphens, colons, semi-colons
def normalizeString(s):
    s = s.strip().lower()
    # Check if hyphens are against single/double quotes (we need to keep the quotes and not add a space)
    if re.search(r'((\'|\")\-+|\-+(\'|\"))', s):
        s = re.sub(r'(\'\-+\s*|\s*\-+\')', '\'', s)
        s = re.sub(r'(\"\-+\s*|\s*\-+\")', '\"', s)
    s = re.sub(r'[\(\)\*\_\\\/,:]', ' ', s) # Punctuations to remove, replace with space
    s = re.sub(r"\s\-+\s", ' ', s) # Replace 1 or more hyphens with spaces
    # Abbreviated words to remove periods from
    s = re.sub(r"mr\.", "mr", s)
    s = re.sub(r"mrs\.", "mrs", s)
    s = re.sub(r"ms\.", "ms", s)
    s = re.sub(r'dr\.', 'dr', s)
    s = re.sub(r'b\.c\.', 'bc', s)
    s = re.sub(r'a\.d\.', 'ad', s)
    return s

# Handle multiple periods by determining if they end a sentence or not
# If they end a sentence, replace with a single period
# If they do not, replace with whitespace
def replace_multiple_periods(lines):
    # Helper function
    def replace_periods(word, replace_text=''):
        return re.sub(r'[\.]{2,}', replace_text, word)

    for i, line in enumerate(lines):
        words = line.strip().split()
        for j, word in enumerate(words):
            # Separate sentences if multiple periods exist based on the following conditions:
            # First char after periods is capital, and not "I" or "I'*".
            if re.search(r'[\.]{2,}', word): # Checks [word]..[.*]
                # Check if this is multiple periods separating two words, no spaces
                if re.search(r'[\.]{2,}\w', word):
                    word_split = re.sub(r'[\.]{2,}', ' ', word).split()
                    word_builder = word_split[0]
                    # Combine the words together, deciding if there should be a period or space
                    for k in range(len(word_split)):
                        if k+1 < len(word_split):
                            # If the word following the periods is capital, and is not "I", "I'*", etc, add a period
                            if re.search(r'^[A-Z]', word_split[k+1]) and not re.search(r'^(I\'.+|I[.!?]*$)', word_split[k+1]):
                                word_builder += '. ' + word_split[k+1]
                            else:
                                word_builder += ' ' + word_split[k+1]
                    # Replace our current word
                    word = word_builder
                # Check the next word
                elif j+1 < len(words):
                    # First char is capital, and not "I", "I'*", etc
                    if re.search(r"^[A-Z]", words[j+1]) and not re.search(r"^(I'.+|I[.!?]*$)", words[j+1]):
                        # Replace "..+" with "."
                        word = replace_periods(word, '.')
                    else:
                        # Replace "..+" with " "
                        word = replace_periods(word)
                else:
                    # Check the next line
                    if i+1 < len(lines):
                        next_words = lines[i+1].strip().split()
                        if len(next_words) > 0:
                            # First char is capital, or begins with dialogue (double quotes)
                            if re.search(r'^[A-Z\"]', next_words[0]):
                                # Replace "..+" with "."
                                word = replace_periods(word, '.')
                            else:
                                # Next sentence begins with a lower case letter, let's assume the sentence continues
                                word = replace_periods(word)
                        else:
                            # Empty line next, assume the sentence ended
                            word = replace_periods(word, '.')
                    else:
                        # EOL, and EOF, replace "..+" with " "
                        word = replace_periods(word)
            elif re.search(r'^(\'|\")?[\.]{2,}\w', word):
                word = replace_periods(word)
            words[j] = word
        lines[i] = ' '.join(words)
    return lines

# Splits character dialogue and "inner" dialogue into separate sentences
def parse_dialogue(lines):
    sentences = []
    currSentence = []
    inDialogue = False
    inInnerDialogue = False
    for i, line in enumerate(lines):
        # Correction for inDialogue bool
        if inDialogue and len(line) == 0:
            inDialogue = False
        if '"' in line:
            line_words = line.split()
            for j, word in enumerate(line_words):
                # Search for dialogue to find double quotes
                if '"' in word:
                    # Special case where double quote is separated as its own token
                    if word == '"':
                        if inDialogue:
                            if len(currSentence) > 0:
                                sentences.append(' '.join(currSentence))
                                currSentence = []
                            inDialogue = False
                        else:
                            # We are not in dialogue, will need to do a few checks
                            # Check if the previous word contained a double quote
                            prev_line_words = []
                            if i > 0:
                                prev_line_words = lines[i-1].split()
                            if (j > 0 and '"' in line_words[j-1]) or \
                                    (j == 0 and len(prev_line_words) > 0 and '"' in prev_line_words[-1]):
                                # Current sentence should be empty, but if not, let's empty it
                                if len(currSentence) > 0:
                                    sentences.append(' '.join(currSentence))
                                    currSentence = []
                                inDialogue = True # Set dialogue for next sentence
                            #elif (j+1 < len(words) and '"' in words[j+1]) or (i+1 < len(words) and '"' in line[i+1].split()[0]):
                            else:
                                # Previous word did not have double quotes, next does.
                                # End current sentence, inDialogue already set to False
                                if len(currSentence) > 0:
                                    sentences.append(' '.join(currSentence))
                                    currSentence = []
                    elif re.match(r'^\".+\"$', word):
                        if not inDialogue:
                            # Remove double quotes from word
                            word = re.sub('"', '', word)
                            # End current sentence if it exists
                            if len(currSentence) > 0:
                                sentences.append(' '.join(currSentence))
                                currSentence = []
                            # Add the single word (with possible terminator split)
                            sentences.append(' '.join(separate_terminator(word)))
                        else:
                            print('Possible incorrect dialogue construction around line [{}]'.format(line))
                            inDialogue = False # Correct dialogue errors?
                    elif re.match(r'^\".+$', word):
                        # Starting dialogue
                        inDialogue = True
                        # An existing sentence was not terminated before entering dialogue
                        if len(currSentence) > 0:
                            sentences.append(' '.join(currSentence)) # Add the sentence
                        word = re.sub('"', '', word)
                        currSentence = [word] # Start a new sentence with the dialogue
                    elif re.match(r'^.+\"$', word):
                        # End of dialogue
                        inDialogue = False
                        # Check if the last word ended in one of our sentence terminators
                        word = re.sub('"', '', word)
                        words = separate_terminator(word)
                        currSentence += words
                        sentences.append(' '.join(currSentence)) # end the current sentence
                        currSentence = []
                    else:
                        print('Double quote inconsistency around line: [{}]'.format(line))
                        # Remove double quote and add word
                        word = re.sub('"', '', word)
                        currSentence.append(word)
                elif '\'' in word:
                    if re.match(r'^\'.+\'$', word):
                        word = re.sub('\'', '', word)
                        # End current sentence if it exists
                        if len(currSentence) > 0:
                            sentences.append(' '.join(currSentence))
                            currSentence = []
                        # Add the single word (with possible terminator split)
                        sentences.append(' '.join(separate_terminator(word)))
                    elif re.match(r'^\'.+$', word):
                        inInnerDialogue = True
                        # An existing sentence was not terminated before entering dialogue
                        if len(currSentence) > 0:
                            sentences.append(' '.join(currSentence)) # Add the sentence
                        word = re.sub('\'', '', word)
                        currSentence = [word] # Start a new sentence with the dialogue
                    elif re.match(r'^.+\'$', word):
                        # Naive check that this is the end of inner dialogue and not a plural possessive word
                        if inInnerDialogue or word[-1] != 's':
                            # End the inner dialogue
                            inInnerDialogue = False
                            word = re.sub('\'', '', word)
                            # Check if the last word ended in one of our sentence terminators
                            words = separate_terminator(word)
                            currSentence += words
                            sentences.append(' '.join(currSentence)) # end the current sentence
                            currSentence = []
                        else:
                            # Potential plural possessive, add it and continue the current sentence
                            word = re.sub('\'', '', word)
                            currSentence.append(word)
                    else:
                        print('Single quote inconsistency around line: [{}]'.format(line))
                        # Remove single quote and add word
                        word = re.sub('\'', '', word)
                        currSentence.append(word)
                else:
                    currSentence.append(word)
        else:
            sentences.append(line)
        
    return sentences

# Separates a terminator with a space to be its own token in the sentence
def separate_terminator(text):
    if re.search(r'[\.!?;]$', text):
        if text[-1] == '!' or text[-1] == '?':
            return [text[:-1], text[-1]]
        else:
            return [text[:-1]]
    else:
        return [text]

# Removes all punctuation from the given lines
def remove_punctuation(lines, replace_str=''):
    for i, line in enumerate(lines):
        # Single quotes are not handled by this as they are a special case and already removed
        lines[i] = re.sub(r'[\"\(\)\-\_\+\=\&\^\$\%\#\@\~\`\.\;\:\\\/\<\>]', replace_str, line)
    return lines

def convert_lines_to_sentences(lines):
    # Tokenize lines
    for i, line in enumerate(lines):
        tokens = word_tokenize(line)
        #tokens = [token for token in tokens if token.lower() not in stops]
        lines[i] = ' '.join(tokens)
    # Separate lines into sentences
    sentences = []
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    for sentence in tokenizer.tokenize('\n'.join(lines)):
        # Replace newlines with spaces
        sentences.append(' '.join(sentence.split('\n')))
    
    return sentences
    """
    try:
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    except Exception:
        nltk.download('punkt')
        tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    """
    """
    try:
        # Convert unicode characters to their nearest ASCII equivalent
        lines = [unidecode(line) for line in lines]
    except:
        print('CONVERSION FAILURE: UNIDECODE')
    """
    """
    try:
        # Use nltk to parse into sentences
        sentences = []
        for sentence in tokenizer.tokenize('\n'.join(lines)):
            # Replace newlines with spaces
            sentences.append(' '.join(sentence.split('\n')))
    except:
        print('CONVERSION FAILURE: nltk tokenize')
    """
    """
    sentences = lines
    try:
        # Parse multiple periods to determine if they end a sentence
        sentences = replace_multiple_periods(sentences)
    except:
        print('CONVERSION FAILURE: multiple periods')
        
    try:
        # Lower and normalize the text
        sentences = [normalizeString(line) for line in sentences]
    except:
        print('CONVERSION FAILURE: normalize string')

    try:
        # Remove all single quotes via the contraction dictionary or predefined contraction pairs
        for i, sentence in enumerate(sentences):
            if '\'' in sentence:
                # Now iterate over the sentence seeing if we can expand out any contractions
                words = sentences[i].split()
                for j, word in enumerate(words):
                    if '\'' in word:
                        # Remove any punctuation from word to expand:
                        word = re.sub(r'[\.\!\?\;\:\"]', '', word)
                        # Check if we can expand out any contractions in the words
                        for contraction_pair in CONTRACTION_PAIRS:
                            regex = r'{}$'.format(contraction_pair[0])
                            if re.search(regex, word):
                                words[j] = re.sub(regex, contraction_pair[1], word)
                sentences[i] = ' '.join(words)
    except:
        print('CONVERSION FAILURE: predefined contractions')

    try:
        # Separate dialogue into its own sentences
        sentences = parse_dialogue(sentences)
    except:
        print('CONVERSION FAILURE: dialogue')

    try:
        # Remove any leftover single quotes
        sentences = [re.sub(r'\'', '', sentence) for sentence in sentences]
    except:
        print('CONVERSION FAILURE: remove single quotes')

    try:
        # Separate terminator tokens into their own sentences ('.', ';', '!', '?') and move ('?' and '!') into their own token
        for i, sentence in enumerate(sentences):
            # Find sentence terminators ('.', ';', !', and '?')
            # Sentence with terminators still in the middle (multiple sentences), or the terminator ending the sentence is
            # still attached to a token
            if re.match(r'^.+[\.!?;].+$', sentence) or re.search(r'\w+[\.!?;]$', sentence):
                parsed_sentence = []
                for word in sentence.split():
                    if re.match(r'\w+[\.!?;]$', word):
                        # Terminator is attached to word
                        words = separate_terminator(word)
                        parsed_sentence += words + ['\n']
                    elif word in ['.', '!', '?', ';']:
                        parsed_sentence += [word, '\n']
                    elif re.search(r'[\.!?;]', word):
                        # Special case of multiple terminators concatenated
                        words = []
                        iters = 0
                        word_len = len(word)
                        while (re.search(r'[\.!?;]{2,}', word)):
                            words += separate_terminator(word)
                            word = ' '.join(words)
                            if iters > word_len:
                                break
                            iters += 1
                        words = separate_terminator(word)
                        parsed_sentence += words
                    else:
                        parsed_sentence.append(word)
                sentences[i] = ' '.join(parsed_sentence)
    except:
        print('CONVERSION FAILURE: terminator separation')
            
    try:
        # Need one final pass to split on newlines gathered in terminator section
        final_sentences = []
        for sentence in sentences:
            final_sentences += [s.strip() for s in sentence.split('\n') if len(s) > 0]
    except:
        print('CONVERSION FAILURE: split on newlines from terminators')

    try:
        # Remove placeholder asterisks with single quotes
        final_sentences = [re.sub(r'\*', '\'', sentence) for sentence in final_sentences]
    except:
        print('CONVERSION FAILURE: removing placeholder asterisks')

    try:
        # Final pass to remove all punctuation
        final_sentences = remove_punctuation(final_sentences)
    except:
        print('CONVERSION FAILURE: remove punctuation (final)')

    return final_sentences
    """
def main():
    lines = []
    filename = None
    for line in sys.stdin:
        line = line.strip()
        if len(line) > 0:
            #line = ' '.join(line.strip().split()[1:]).lower()
            # Check if this is being ran outside of Hadoop
            line_split = line.split()
            # Pos 0  = byte offset
            # Pos 1  = filename
            # Pos 2+ = line
            #try:
            if filename is None:
                filename = line_split[1]
            line = ' '.join(line_split[2:]).lower()
            #except:
            #print('REDUCER FAIL SPLIT: [{}]'.format(line))
            
            #line = '\t'.join(line.strip().split('\t')[1:]).lower()
            # Skip empty lines
            if len(line) > 0:
                lines.append(line)
    #converted = True
    try:
        sentences = convert_lines_to_sentences(lines)
    except Exception as e:
        print('CONVERSION FAILURE: [{}]'.format(repr(e)))
        return
    #converted = False
    #if converted:
    #try:
    for i, sentence in enumerate(sentences):
        # Format: <filname>\t<sentence index>\t<sentence>
        print('{}\t{}\t{}'.format(filename, i, sentence))
    #except:
    #print('SENTENCE OUTPUT FAILURE')
    #else:
    #print('SENTENCE CONVERSION FAILURE: ELSE')

# Old code for blocking:
"""
        #filename, line = line.split('\t', 1)
        in_single_sentence = False
        if len(curr_block) == 0:
            curr_block = [line]
            in_single_sentence = True
        elif line[0] == '"':
            # End the previous block
            print('{}\t{}'.format('{},{}'.format(block_count, filename), ' '.join(curr_block)))
            curr_block = [line]
            block_count += 1
            in_single_sentence = True
        # Check if this line ends a sentence
        if line[-1] in SENTENCE_ENDINGS:
            # Check that it's not a period and one of our abbreviations
            if line[-1] == '.' and line.split()[-1] in ABBREVIATIONS:
                # Remove the period
                line = line[:-1]
                # Add line to block and continue to next iteration
                curr_block.append(line)
                continue
            # End the current block
            if not in_single_sentence:
                # Because we've already added this line to curr_block
                curr_block.append(line)
            print('{}\t{}'.format('{},{}'.format(block_count, filename), ' '.join(curr_block)))
            curr_block = []
            block_count += 1
        elif not in_single_sentence:
            curr_block.append(line)
"""

if __name__ == '__main__':
    main()