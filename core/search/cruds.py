from . import indexers
from . import schemes
import whoosh.index
import whoosh.qparser
import whoosh.query
from config import ITEMS_PER_PAGE


class SearchCRUD:
    def __init__(self, scheme, indexer: whoosh.index.FileIndex, fields: list[str]):
        self.indexer = indexer
        self.scheme = scheme
        self.fields = fields

    def create(self, data: dict):
        writer = self.indexer.writer()
        writer.add_document(**data)
        writer.commit()

    def search(self, query: str, page: int):
        results = []
        with self.indexer.searcher() as searcher:
            for field in self.fields:
                qp = whoosh.qparser.QueryParser(
                    field, self.scheme, termclass=whoosh.query.FuzzyTerm)
                q = qp.parse(query)

                results += list(map(lambda item: dict(item),
                                searcher.search_page(q, page, pagelen=ITEMS_PER_PAGE)))

        return results

    def update(self, id_: int, data: dict):
        writer = self.indexer.writer()
        writer.update_document(id=str(id_), **data)
        writer.commit()

    def delete(self, id_: int):
        writer = self.indexer.writer()
        writer.delete_by_term('id', str(id_))
        writer.commit()

    def get_all_indices(self):
        with self.indexer.searcher() as searcher:
            return list(searcher.documents())


class BookCRUD(SearchCRUD):
    def __init__(self):
        fields = [
            'title',
            'description',
            'authors'
        ]
        super().__init__(schemes.book_scheme, indexers.book_indexer, fields)


class UserCRUD(SearchCRUD):
    def __init__(self):
        fields = [
            'name',
            'middlename',
            'surname',
            'login'
        ]
        super().__init__(indexers.schemes.user_scheme, indexers.user_indexer, fields)
