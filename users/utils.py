from . import schemes
from config import ITEMS_PER_PAGE
from sqlalchemy.orm import Session
from auth.utils import create_user, get_max_user_id
import datetime as dt
from models import User


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


async def handle_users(line: list, db: Session, result: list):
    max_id = await get_max_user_id(db)
    user = dict(zip(['name', 'middlename', 'surname', 'birthdate', 'year_of_study'], line))
    if '.' in user['birthdate']:
        user['birthdate'] = dt.datetime.strptime(user['birthdate'], '%d.%m.%Y').date()
    else:
        user['birthdate'] = dt.datetime.fromisoformat(user['birthdate']).date()
    result.append(await create_user(user, db, max_id))


async def user_write_func(user: User):
    return [
        user.login,
        user.name,
        user.middlename,
        user.surname,
        user.birthdate,
        user.year_of_study,
        user.rights
    ]
