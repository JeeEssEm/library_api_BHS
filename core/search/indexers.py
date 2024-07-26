import os
import whoosh.index
from config import SEARCHER_PATH
from . import schemes


if not os.path.exists(SEARCHER_PATH):
    os.mkdir(SEARCHER_PATH)

book_folder = SEARCHER_PATH / 'books'
user_folder = SEARCHER_PATH / 'users'

if not os.path.exists(book_folder):
    os.mkdir(book_folder)
    ix = whoosh.index.create_in(book_folder, schemes.book_scheme)

if not os.path.exists(user_folder):
    os.mkdir(user_folder)
    ix = whoosh.index.create_in(user_folder, schemes.user_scheme)


book_indexer = whoosh.index.open_dir(book_folder)
user_indexer = whoosh.index.open_dir(user_folder)
