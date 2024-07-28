import whoosh.fields


user_scheme = whoosh.fields.Schema(
    id=whoosh.fields.ID(unique=True, stored=True),
    name=whoosh.fields.TEXT(stored=True),
    middlename=whoosh.fields.TEXT(stored=True),
    surname=whoosh.fields.TEXT(stored=True),
    login=whoosh.fields.TEXT(stored=True)
)

book_scheme = whoosh.fields.Schema(
    id=whoosh.fields.ID(unique=True, stored=True),
    title=whoosh.fields.TEXT(stored=True),
    description=whoosh.fields.TEXT(stored=True),
    authors=whoosh.fields.TEXT(stored=True)
)
