from .schemes import book_index, book_searcher, user_index, user_searcher
import tantivy


class SearchCRUD:
    def __init__(self, indexer, searcher):
        self.indexer = indexer
        self.searcher = searcher

    def update(self):
        ...

    def create(self, data: dict):
        writer = self.indexer.writer()
        writer.add_document(tantivy.Document(**data))
        writer.commit()
        writer.wait_merging_threads()
        self.indexer.reload()

    def delete(self, id_: int):
        writer = self.indexer.writer()
        writer.delete_documents('id', id_)
        writer.commit()

    def search(self, query: str):
        q = self.indexer.parse_query(query)
        hits = self.searcher.search(q).hits
        print(hits)
        if hits:
            return list(map(lambda item: self.searcher.doc(item[1])['id'][0], hits))
        return []


class BookCRUD(SearchCRUD):
    def __init__(self):
        super().__init__(book_index, book_searcher)


class UserCRUD(SearchCRUD):
    def __init__(self):
        super().__init__(user_index, user_searcher)
