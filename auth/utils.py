import fastapi
from typing import Annotated
import core.security
import models
import jwt
from sqlalchemy.orm import Session
import sqlalchemy
from core.db import get_db
from core.search.cruds import UserCRUD as UserSearchCRUD

oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl='auth/login')


async def get_current_user(
        token:
        Annotated[str, fastapi.Depends(oauth2_scheme)],
        db: Annotated[Session, fastapi.Depends(get_db)]):
    try:
        data = core.security.decode_token(token)
        user = db.query(models.User).filter(
            models.User.id == data.get('id')).first()
        return user
    except jwt.exceptions.ExpiredSignatureError:
        raise fastapi.exceptions.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail='Token expired'
        )


async def is_authenticated(request: fastapi.Request):
    return request.headers.get('Authorization') is not None


async def create_user(user, db, max_id):
    try:
        name = user.get('name')
        surname = user.get('surname')
        middlename = user.get('middlename')
        year_of_study = int(user.get('year_of_study'))
        birthdate = user.get('birthdate')
        rights = user.get('rights') or models.Rights.student

        login = core.security.generate_login(max_id)
        password = core.security.generate_random_password()
        user_model = models.User(
            name=name, surname=surname, middlename=middlename,
            year_of_study=year_of_study, birthdate=birthdate,
            login=login,
            password=core.security.get_password_hash(password),
            rights=rights
        )

        db.add(user_model)
        db.commit()

        UserSearchCRUD().create({
            'id': str(max_id),
            'name': name,
            'middlename': middlename,
            'surname': surname,
            'login': login,
        })

        return {
            'name': name,
            'middlename': middlename,
            'surname': surname,
            'login': login,
            'password': password
        }

    except Exception as exc:
        raise core.exceptions.SomethingWentWrongException(exc)


async def get_max_user_id(db: Session):
    max_id = db.query(models.User, sqlalchemy.func.max(
        models.User.id)).first()[1]
    if not max_id:
        max_id = 0
    max_id += 1
    return max_id


async def create_users(users: list, db: Session):
    max_id = await get_max_user_id(db)

    result = []
    for user in users:
        result.append(await create_user(dict(user), db, max_id))
        max_id += 1
    return result
