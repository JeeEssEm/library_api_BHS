import tantivy
from config import SEARCHER_PATH
import os

# if not os.path.exists(SEARCHER_PATH):
#     os.mkdir(SEARCHER_PATH)

book_folder = SEARCHER_PATH / 'books'
user_folder = SEARCHER_PATH / 'users'

if not os.path.exists(book_folder):
    os.mkdir(book_folder)

if not os.path.exists(user_folder):
    os.mkdir(user_folder)


book_builder = tantivy.SchemaBuilder()
book_builder.add_integer_field('id', stored=True)
book_builder.add_text_field('title', stored=True)
book_builder.add_text_field('description', stored=True)
book_builder.add_text_field('authors', stored=True)
book_schema = book_builder.build()

user_builder = tantivy.SchemaBuilder()
user_builder.add_integer_field('id', stored=True)
user_builder.add_text_field('name', stored=True)
user_builder.add_text_field('middlename', stored=True)
user_builder.add_text_field('surname', stored=True)
user_builder.add_text_field('login', stored=True)
user_schema = user_builder.build()


book_index = tantivy.Index(book_schema, str(book_folder))
user_index = tantivy.Index(user_schema, str(user_folder))

book_searcher = book_index.searcher()
user_searcher = user_index.searcher()

# book_writer = book_index.writer()
# book_writer.add_document(tantivy.Document(**{
#     'id': 1,
#     'title': ['Go lang basics'],
#     'description': ['Develop seamless, efficient, and robust microservices with Go'],
#     'authors': ['Nic Jackson']
# }))
# book_writer.commit()
