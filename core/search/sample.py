import tempfile
import pathlib
import tantivy

# Declaring our schema.
schema_builder = tantivy.SchemaBuilder()
schema_builder.add_text_field("title", stored=True)
schema_builder.add_text_field("body", stored=True)
schema_builder.add_integer_field("doc_id", stored=True)
schema = schema_builder.build()

# Creating our index (in memory)
# index = tantivy.Index(schema)


# tmpdir = tempfile.TemporaryDirectory()
index_path = STATIC_PATH = pathlib.Path(__file__).resolve().parent / 'index'
# index_path.mkdir()

persistent_index = tantivy.Index(schema, path=str(index_path))


writer = persistent_index.writer()
writer.delete_all_documents()
writer.commit()
# writer.add_document(tantivy.Document(
#     doc_id=1,
#     title=["The Old Man and the Sea"],
#     body=["""He was an old man who fished alone in a skiff in the Gulf Stream and he had gone eighty-four days now without taking a fish."""],
# ))
# # ... and committing
# writer.commit()
# writer.wait_merging_threads()


# persistent_index.reload()
# searcher = persistent_index.searcher()


# query = persistent_index.parse_query("fish days", ["title", "body"])
# (best_score, best_doc_address) = searcher.search(query, 3).hits[0]
# best_doc = searcher.doc(best_doc_address)
# print(best_doc['title'], best_doc['body'])

# print(searcher.search(query, 3).hits[0])


