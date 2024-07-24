import fastapi
from typing import Annotated
import models
from core.db import get_db
from sqlalchemy.orm import Session
from auth import schemes as auth_schemes
from auth.utils import get_current_user
import core.validators
from .utils import paginate, converter_user_search
import core.exceptions

router = fastapi.APIRouter()


@router.get('/{user_id}', response_model=auth_schemes.User)
async def get_user(user_id: int,
                   current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                   db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user) or user_id == current_user.id:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise core.exceptions.UserDoesNotExistException()

        return {
            'name': user.name or '******',
            'surname': user.surname or '******',
            'middlename': user.middlename or '******',
            'year_of_study': user.year_of_study or '1',
            'birthdate': user.birthdate or '1997-01-01',
            'rights': user.rights or models.Rights.admin
        }
    raise core.exceptions.NotEnoughRightsException()


@router.put('/edit/{user_id}')
async def edit_user(user_id: int,
                    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                    form: Annotated[auth_schemes.User, fastapi.Depends()],
                    db: Session = fastapi.Depends(get_db)):
    
    if await core.validators.is_admin(current_user):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if user is None:
            raise core.exceptions.UserDoesNotExistException()
        user.name = form.name or user.name
        user.surname = form.surname or user.surname
        user.middlename = form.middlename or user.middlename
        user.birthdate = form.birthdate or user.birthdate
        user.year_of_study = form.year_of_study or user.year_of_study
        user.rights = form.rights or user.rights 
        try:
            db.add(user)
            db.commit()
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.post('/search/{page}')
async def search_user(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      form: Annotated[auth_schemes.User, fastapi.Depends()], page: int,
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        users = db.query(models.User)
        if form.name:
            users = users.filter(models.User.name.like(f'%{form.name}%'))
        if form.surname:
            users = users.filter(models.User.surname.like(f'%{form.surname}%'))
        if form.middlename:
            users = users.filter(models.User.middlename.like(f'%{form.middlename}%'))

        if form.birthdate:
            users = users.filter(models.User.birthdate.like(f'%{form.birthdate}%'))
        if form.year_of_study:
            users = users.filter(models.User.year_of_study == form.year_of_study)

        if await core.validators.is_admin(current_user) and form.rights:
            users = users.filter(models.User.rights == form.rights)

        return paginate(page, users, converter_user_search)

    raise core.exceptions.NotEnoughRightsException()


@router.delete('/delete/{user_id}')
async def delete_user(user_id: int,
                      current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_admin(current_user):
        q = db.query(models.User).filter(models.User.id == user_id)
        if q.first() is None:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='User doesn\'t exist!'
            )
        try:
            if len(q.first().books) != 0:
                raise fastapi.exceptions.HTTPException(
                    status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='User hasn\'t returned all books!'
                )
            q.delete()
            db.commit()
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()
