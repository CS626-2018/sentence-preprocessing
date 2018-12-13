# download_books.py

import os
import re
from string import ascii_lowercase
import urllib.request as url

from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers

BOOK_FILE_FORMAT = 'data/books/{}.txt'
BOOK_IDS_FILE = 'data/book_ids.txt'
BOOKS_URL = 'https://www.gutenberg.org/browse/titles/{}'

book_ids = set()

# If the book ids file exists, read the ids into the set
if os.path.isfile(BOOK_IDS_FILE):
    with open(BOOK_IDS_FILE) as f:
        for line in f.readlines():
            book_ids.add(int(line))
elif not os.path.exists(os.path.dirname(BOOK_IDS_FILE)):
    os.makedirs(os.path.dirname(BOOK_IDS_FILE))

# Iterate over books starting with A-Z
for letter in ascii_lowercase:
    with url.urlopen(BOOKS_URL.format(letter)) as response:
        for line in response.readlines():
            line = line.decode()
            # Search for the ID of english books
            r = re.search('href="/ebooks/(\d+)">.*\(English\)', line)
            if r:
                # Try adding the book id to the set
                try:
                    book_ids.add(int(r.group(1)))
                except ValueError as e:
                    print(repr(e))

# Overwrite the book ids file with the updated list of book ids
with open(BOOK_IDS_FILE, 'w+') as f:
    for i, book_id in enumerate(book_ids):
        f.write(str(book_id))
        if i+1 < len(book_ids):
            f.write('\n')

# For each id, write the book to its own file if it doesn't exist
if not os.path.exists(os.path.dirname(BOOK_FILE_FORMAT)):
    os.makedirs(os.path.dirname(BOOK_FILE_FORMAT))

num_downloaded = 0
num_existing = 0
for book_id in book_ids:
    if not os.path.isfile(BOOK_FILE_FORMAT.format(book_id)):
        try:
            book_text = strip_headers(load_etext(book_id)).strip()
            with open(BOOK_FILE_FORMAT.format(book_id), 'w+') as f:
                f.write(book_text)
            print('Book {} downloaded.'.format(book_id))
            num_downloaded += 1
        except Exception as e:
            print(repr(e))
    else:
        print('Book {} already exists.'.format(book_id))
        num_existing += 1

print('Downloaded {}/{} new books.'.format(num_downloaded, len(book_ids) - num_existing))

