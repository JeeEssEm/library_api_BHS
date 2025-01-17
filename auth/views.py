from core.db import get_db
import models
import fastapi
import core.security
import core.validators
import core.exceptions
from . import schemes
from .utils import get_current_user, create_users
from typing import Annotated
from sqlalchemy.orm import Session


router = fastapi.APIRouter()


@router.post(
    '/login', response_model=schemes.TokenResponseModel,
    summary='Login using login (username field) and password',
)
async def login(
    response: fastapi.Response,
    form_data: Annotated[
        fastapi.security.OAuth2PasswordRequestForm,
        fastapi.Depends()],
        db: Session = fastapi.Depends(get_db)
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


@router.post(
    '/create', response_model=schemes.CreateUsersResponseModel,
    summary='Create users by uploading a list of users with specified data',
    description='''
Send request with list of user with data
 (name, middlename, surname, year of study, birthdate and rights)
and get list with automatically generated logins and passwords for these users.\n
__Note:__
- _birthdate_ field can be only in this format: _"{year}-{month}-{day}"_ (ex. 2000-12-30)
- _year of study_ field can be integer in range from 1 to 11
- _rights_ field can be only one of available values (student/librarian/admin)
    '''
)
async def create_users_route(
        form_data: schemes.CreateUsersRequestModel,
        current_user: Annotated[
            models.User, fastapi.Depends(get_current_user)
        ],
        db: Session = fastapi.Depends(get_db)):
    if not await core.validators.is_admin(current_user):
        raise core.exceptions.NotEnoughRightsException()

    result = await create_users(form_data.users, db)

    return schemes.CreateUsersResponseModel(
        users=result
    )


@router.post(
    '/update_token',
    response_model=schemes.TokenResponseModel,
    summary='Refresh access token',
    description='Just send request (refresh token must be in cookies) and get new access token'
)
async def update_token(request: fastapi.Request, response: fastapi.Response,
                       db: Session = fastapi.Depends(get_db)):
    refresh_token = request.cookies.get('refresh_token')

    if core.security.is_valid_token(refresh_token):
        current_user = await get_current_user(refresh_token, db)
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


@router.get(
    '/whoami',
    response_model=schemes.WhoamiResponseModel,
    summary='Get information about current user')
async def whoami(current_user:
                 Annotated[models.User, fastapi.Depends(get_current_user)]):
    return schemes.WhoamiResponseModel(
        login=current_user.login,
        name=current_user.name or '*******',
        surname=current_user.surname or '*******',
        middlename=current_user.middlename or '*******',
        birthdate=current_user.birthdate or '1997-01-01',
        year_of_study=current_user.year_of_study or '11',
        rights=current_user.rights or models.Rights.student,
    )


@router.put(
    '/change_password/{user_id}',
    description='Change user\'s password. Only __admin__ can do this! No one else!'
)
async def change_password(user_id: int,
                          current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                          form: Annotated[schemes.ChangePasswordRequestForm, fastapi.Depends()],
                          db: Session = fastapi.Depends(get_db)):

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
