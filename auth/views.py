from db import db
import models
import fastapi
import core.security
import core.validators
import core.exceptions
import sqlalchemy
from . import schemes
from .utils import get_current_user
from typing import Annotated


router = fastapi.APIRouter()


@router.post('/login', response_model=schemes.TokenResponseModel)
async def login(
    response: fastapi.Response,
    form_data: Annotated[
        fastapi.security.OAuth2PasswordRequestForm,
        fastapi.Depends()]
):
    login = form_data.username
    password = form_data.password
    user = db.query(models.User).filter(models.User.login == login).first()

    if user is None or not core.security.verify_password(
        password, user.password
    ):

        raise fastapi.exceptions.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect password or login'
        )
    tokens = core.security.create_tokens(user.id)
    response.set_cookie(key='refresh_token',
                        value=tokens['refresh_token'], httponly=True)
    response.headers['Authorization'] = f'Bearer {tokens["access_token"]}'
    return schemes.TokenResponseModel(
        access_token=tokens['access_token'],
        token_type='bearer'
    )


@router.post('/create', response_model=schemes.CreateUsersResponseModel)
async def create_users(
        form_data: schemes.CreateUsersRequestModel,
        current_user: Annotated[
            models.User, fastapi.Depends(get_current_user)
        ]):
    if not await core.validators.is_admin(current_user):
        raise core.exceptions.NotEnoughRightsException()

    max_id = db.query(models.User, sqlalchemy.func.max(
        models.User.id)).first()[1]
    if not max_id:
        max_id = 0
    max_id += 1
    data = form_data.users
    result = []
    for user in data:
        try:
            name = user.name
            surname = user.surname
            middlename = user.middlename
            year_of_study = int(user.year_of_study)
            birthdate = user.birthdate
            rights = user.rights

            login = core.security.generate_login(max_id)
            max_id += 1
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

            result.append({
                'name': name,
                'middlename': middlename,
                'surname': surname,
                'login': login,
                'password': password
            })

        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)
    return schemes.CreateUsersResponseModel(
        users=result
    )


@router.post('/update_token', response_model=schemes.TokenResponseModel)
async def update_token(request: fastapi.Request, response: fastapi.Response):
    refresh_token = request.cookies.get('refresh_token')

    if core.security.is_valid_token(refresh_token):
        current_user = await get_current_user(refresh_token)
        tokens = core.security.create_tokens(current_user.id)
        response.headers['Authorization'] = f'Bearer {tokens["access_token"]}'
        return schemes.TokenResponseModel(
            access_token=tokens['access_token'],
            token_type='bearer'
        )

    raise fastapi.exceptions.HTTPException(
        status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
        detail='Invalid token or token expired'
    )


@router.get('/whoami', response_model=schemes.WhoamiResponseModel)
async def whoami(current_user:
                 Annotated[models.User, fastapi.Depends(get_current_user)]):
    return schemes.WhoamiResponseModel(
        login=current_user.login,
        name=current_user.name or '*******',
        surname=current_user.surname or '*******',
        middlename=current_user.middlename or '*******',
        birthdate=current_user.birthdate or '1997-01-01',
        year_of_study=current_user.year_of_study or '11',
        rights=current_user.rights,
    )


@router.put('/change_password/{user_id}')
async def change_password(user_id: int,
                          current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                          form: Annotated[schemes.ChangePasswordRequestForm, fastapi.Depends()]):

    if await core.validators.is_admin(current_user):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise core.exceptions.UserDoesNotExistException()

        user.password = core.security.get_password_hash(form.new_password)
        try:
            db.add(user)
            db.commit()
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()