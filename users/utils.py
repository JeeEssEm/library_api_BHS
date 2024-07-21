from . import schemes
from config import ITEMS_PER_PAGE


def paginate(page, query, scheme_converter):
    paginated_query = query.offset((page - 1) * ITEMS_PER_PAGE).limit(ITEMS_PER_PAGE).all()
    return schemes.PageResponseModel(
        total=query.count(),
        page=page,
        size=ITEMS_PER_PAGE,
        results=list(map(lambda item: scheme_converter(item), paginated_query))
    )


def converter_user_search(user_model):
    return schemes.UserSearch(
        id=user_model.id,
        name=user_model.name or '*******',
        surname=user_model.surname or '*******',
        middlename=user_model.middlename or '*******',
        rights=user_model.rights
    )
