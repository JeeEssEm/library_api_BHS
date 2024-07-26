import fastapi
from typing import Annotated
import models
from core.db import get_db
from sqlalchemy.orm import Session
from auth import schemes as auth_schemes
from auth.utils import get_current_user
import core.validators
from .utils import paginate, converter_user_search, handle_users, user_write_func
from books.utils import write_to_csv, remove_file
import core.exceptions
from books.utils import handle_csv
from core.search.cruds import UserCRUD as UserSearchCRUD

router = fastapi.APIRouter()


@router.get('/info/{user_id}', response_model=auth_schemes.User)
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

            UserSearchCRUD().update(user.id, {
                'name': user.name,
                'middlename': user.middlename,
                'surname': user.surname,
                'login': user.login,
            })
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.post('/search/{page}')
async def search_user(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      page: int,
                      query: str = None,
                      year_of_study: int = None,
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        ids = []
        users_query = db.query(models.User)
        if query:
            ids = list(map(lambda item: int(item['id']), UserSearchCRUD().search(query, page)))
            if not ids:
                users_query = users_query.filter(False)
            else:
                users_query = users_query.filter(models.User.id.in_(ids))

            if year_of_study:
                users_query = users_query.filter(models.User.year_of_study == year_of_study)

        return paginate(page, users_query, converter_user_search)

    raise core.exceptions.NotEnoughRightsException()


@router.delete('/delete/{user_id}')
async def delete_user(user_id: int,
                      current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_admin(current_user):
        q = db.query(models.User).filter(models.User.id == user_id)
        user = q.first()
        if user is None:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='User doesn\'t exist!'
            )
        try:
            if len(user.books) != 0:
                raise fastapi.exceptions.HTTPException(
                    status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail='User hasn\'t returned all books!'
                )
            UserSearchCRUD().delete(user.id)
            q.delete()
            db.commit()
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.post('/load_csv', response_model=auth_schemes.CreateUsersResponseModel)
async def load_users_csv(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                         csv_file: fastapi.UploadFile,
                         db: Session = fastapi.Depends(get_db)):
    """ File format (.csv):
    delimiter = ";"
    Columns (only in this order!):
    ___
    Name | Middlename | Surname | Birthdate (2000-12-30 or 30.12.2000) | year_of_study
    """
    if await core.validators.is_admin(current_user):
        try:
            result = []
            await handle_csv(file=csv_file, handle_func=handle_users, db=db, result=result)
            return {'users': result}
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.get('/profiles_csv')
async def get_users_profiles(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    background_tasks: fastapi.BackgroundTasks,
    db: Session = fastapi.Depends(get_db)
):
    if await core.validators.is_admin(current_user):
        users = db.query(models.User).all()
        header = ['login', 'Name', 'Middlename', 'Surname', 'Birthdate', 'Year_of_study']
        path = await write_to_csv(users, user_write_func, header)
        background_tasks.add_task(remove_file, path)
        return fastapi.responses.FileResponse(path, media_type='text/csv')

    raise core.exceptions.NotEnoughRightsException()
