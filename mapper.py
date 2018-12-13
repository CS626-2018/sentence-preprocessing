# mapper.py
# Ryan Zembrodt
# Lines to sentences code partially taken/modified from project with Dr. Harrison

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

# Pre-defined contractions to keep
CONTRACTIONS = [
    'n\'t', '\'ll', '\'s', '\'re', '\'m', '\'d', '\'ve'
]

# Sentence parsing methods
# Removes unneeded punctuation in the data:
# hyphens between words, ex: A -- B -> A B
# commas, double quotes, hyphens, colons, semi-colons
def normalizeString(s):
    s = s.strip().lower()
    # Check if hyphens are against single/double quotes (we need to keep the quotes and not add a space)
    if re.search(r'((\'|\")\-+|\-+(\'|\"))', s):
        s = re.sub(r'(\'\-+\s*|\s*\-+\')', '\'', s)
        s = re.sub(r'(\"\-+\s*|\s*\-+\")', '\"', s)
    s = re.sub(r'[\(\)\*\_\\\/\-,:]', ' ', s) # Punctuations to remove, replace with space
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
                        # Remove double quote and add word
                        word = re.sub('"', '', word)
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

def convert_lines_to_sentences(filename, chunk_index, lines):
    # Convert unicode characters to their nearest ASCII equivalent
    lines = [unidecode(line) for line in lines]
    
    # Use nltk to parse into sentences
    sentences = []
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    for sentence in tokenizer.tokenize('\\'.join(lines)):
        # Replace backslashes with spaces
        sentences.append(' '.join(sentence.split('\\')))

    # Parse multiple periods to determine if they end a sentence
    sentences = replace_multiple_periods(sentences)
        
    # Replace double single quotes with double quotes
    sentences = [re.sub(r'\'\'', '"', sentence) for sentence in sentences]

    
    # Lower and normalize the text
    sentences = [normalizeString(line) for line in sentences]

    # Tokenize the sentences
    for i, sentence in enumerate(sentences):
        sentence = ' '.join(word_tokenize(sentence))
        sentence = re.sub(r'(\'\'|\`\`)', '"', sentence)
        sentence = re.sub(r'\s\'\s', ' " ', sentence)
        # Append backslashes on terminators to split on later
        sentence = re.sub(r'\s\!\s', ' !\\ ', sentence)
        sentence = re.sub(r'\s\?\s', ' ?\\ ', sentence)
        sentence = re.sub(r'\s[\.\;]\s', ' \\ ', sentence)
        sentences[i] = sentence

    # Repleace known contractions with asterisks for placeholders
    for i, sentence in enumerate(sentences):
        if '\'' in sentence:
            words = sentence.split()
            for j, word in enumerate(words):
                if '\'' in word:
                    # Check if we have a known contraction, otherwise remove the single quote
                    if word in CONTRACTIONS:
                        words[j] = re.sub(r'\'', '*', word)
                    else:
                        words[j] = re.sub(r'\'', '', word)
            sentences[i] = ' '.join(words)

    # Separate dialogue into its own sentences
    sentences = parse_dialogue(sentences)
    
    # Remove any leftover single quotes
    #sentences = [re.sub(r'\'', '', sentence) for sentence in sentences]
    
    # Need one final pass to split on backslashes gathered in terminator section
    final_sentences = []
    for sentence in sentences:
        final_sentences += [s.strip() for s in sentence.split('\\') if len(s) > 0]

    # Remove placeholder asterisks with single quotes
    # Final pass to remove all punctuation
    final_sentences = remove_punctuation([re.sub(r'\*', '\'', sentence) for sentence in final_sentences])
    
    # Output to reducer
    print('{}\t{}\t{}'.format(filename, chunk_index, '\\'.join(final_sentences)))

def main(argv):
    local = False
    if len(argv) > 0 and argv[0] == '--local':
        local = True
    #lines = []
    #filename = None
    line_chunk = []
    chunk_count = 0
    curr_file = None

    for line in sys.stdin:
        line = line.strip()
        if len(line) > 0:
            try:
                # Check if this is being ran outside of Hadoop
                line_split = None
                if not local:
                    # We're on Hadoop
                    line_split = line.split()
                else:
                    line_split = ['', 'local', line]
                # Ignore lines with no content
                if len(line_split < 3):
                    continue
                # Pos 0  = byte offset
                # Pos 1  = filename
                # Pos 2+ = line
                filename = line_split[1]
                line_parsed = ' '.join(line_split[2:]).strip()
                if curr_file is None:
                    curr_file = filename

                # Skip empty lines
                #if len(line_parsed) > 0:
                # Check if ends a chunk
                if line_parsed[-1] in ('.', '!', '?') or len(line_parsed) == 0 or curr_file != filename:
                    if len(line_parsed) > 0 :
                        if curr_file != filename:
                            # End current chunk
                            convert_lines_to_sentences(curr_file, chunk_count, line_chunk)
                            # Start new chunk for new file
                            line_chunk = [line_parsed]
                            chunk_count = 0
                            curr_file = filename
                        else:
                            # End current chunk
                            line_chunk.append(line_parsed)
                            convert_lines_to_sentences(curr_file, chunk_count, line_chunk)
                            # Start new chunk for same file
                            line_chunk = []
                            chunk_count += 1
                    else:
                        convert_lines_to_sentences(curr_file, chunk_count, line_chunk)
                        line_chunk = []
                        chunk_count += 1
                else:
                    line_chunk.append(line_parsed)
            except Exception as e:
                print('Line: {}, exception: {}'.format(line, repr(e)))

if __name__ == '__main__':
    main(sys.argv[1:])