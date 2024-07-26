import fastapi
from core.db import get_db
import models
import core.exceptions
import core.validators
from . import schemes as book_schemes
from typing import Annotated, Optional, List
from auth.utils import get_current_user
from sqlalchemy.orm import Session
from .utils import (save_image, delete_image, converter_book_scheme,
                    handle_books, remove_book_image, handle_csv, write_to_csv, book_write_func,
                    remove_file)
from config import STATIC_PATH
from users.utils import paginate
import os
from core.search.cruds import BookCRUD as BookSearchCRUD

router = fastapi.APIRouter()


@router.get('/info/{book_id}', response_model=book_schemes.BookResponseModel)
async def get_book(book_id: int,
                   current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                   db: Session = fastapi.Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    if not book or (book.is_private and not await core.validators.is_librarian(current_user)):
        raise core.exceptions.BookDoesNotExistException()

    in_stock = (
        book.amount -
        db.query(models.BookCarriers).filter(models.BookCarriers.c.book_id == book_id).count()
    )

    return book_schemes.BookResponseModel(
        title=book.title,
        authors=book.authors,
        description=book.description,
        edition_date=book.edition_date,
        in_stock=in_stock,
        is_private=book.is_private,
    )


@router.get('/media/{book_id}', response_class=fastapi.responses.FileResponse)
async def get_book_image(book_id: int,
                         current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                         db: Session = fastapi.Depends(get_db)
                         ):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()

    if not book or (book.is_private and not await core.validators.is_librarian(current_user)):
        raise core.exceptions.BookDoesNotExistException()

    if not book.image:
        path = STATIC_PATH / 'images' / 'not_found.webp'
        if os.path.exists(path):
            return fastapi.responses.FileResponse(path, media_type='image/webp')

        raise fastapi.exceptions.HTTPException(
            status_code=fastapi.status.HTTP_404_NOT_FOUND,
            detail='Image doesn\'t exist')

    path = STATIC_PATH / 'images' / book.image
    ext = book.image.split('.')[-1]

    if os.path.exists(path):
        return fastapi.responses.FileResponse(path, media_type=f'image/{ext}')

    raise fastapi.exceptions.HTTPException(
        status_code=fastapi.status.HTTP_404_NOT_FOUND,
        detail='Image doesn\'t exist')


@router.post('/create_book')
async def create_book(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      form: Annotated[book_schemes.BookCreateRequestForm, fastapi.Depends()],
                      image: Optional[fastapi.UploadFile] = fastapi.File(
                          None, media_type='image/webp'),
                      db: Session = fastapi.Depends(get_db),
                      ):
    if await core.validators.is_librarian(current_user):
        book = models.Book(
            title=form.title,
            authors=form.authors,
            description=form.description,
            edition_date=form.edition_date,
            is_private=form.is_private,
            amount=form.amount,
        )

        if image:
            filename = await save_image(image)
            book.image = filename

        db.add(book)
        db.commit()

        BookSearchCRUD().create({
            'id': book.id,
            'title': book.title,
            'description': book.description,
            'authors': book.authors
        })

        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.put('/edit/{book_id}')
async def edit_book(book_id: int,
                    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                    form: Annotated[book_schemes.BookEditRequestForm, fastapi.Depends()],
                    image: Optional[fastapi.UploadFile] = fastapi.File(
                        None, media_type='image/webp'),
                    db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        book = db.query(models.Book).filter(models.Book.id == book_id).first()
        if book is None:
            raise core.exceptions.BookDoesNotExistException()

        if image is not None:
            if book.image is not None:
                await delete_image(book.image)
            filename = await save_image(image)
            book.image = filename

        book.title = form.title or book.title
        book.description = form.description or book.description
        book.amount = form.amount or book.amount
        book.authors = form.authors or book.authors
        book.is_private = form.is_private or book.is_private
        book.edition_date = form.edition_date or book.edition_date

        db.add(book)
        db.commit()
        return fastapi.status.HTTP_200_OK
    raise core.exceptions.NotEnoughRightsException()


@router.delete('/delete/{book_id}')
async def delete_book(book_id: int,
                      current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        query = db.query(models.Book).filter(models.Book.id == book_id)
        book = query.first()
        if book is None:
            raise core.exceptions.BookDoesNotExistException()
        if len(book.owners) != 0:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Book has owners!'
            )
        if book.image:
            await remove_book_image(book.image)
        BookSearchCRUD().delete(book.id)
        query.delete()
        db.commit()

        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.post('/give_book')
async def give_user_book(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                         form: Annotated[book_schemes.GiveReturnBookForm, fastapi.Depends()],
                         db: Session = fastapi.Depends(get_db)
                         ):
    if await core.validators.is_librarian(current_user):
        user = db.query(models.User).filter(models.User.id == form.user_id).first()
        book = db.query(models.Book).filter(models.Book.id == form.book_id).first()

        if not user:
            raise core.exceptions.UserDoesNotExistException()
        if not book:
            raise core.exceptions.BookDoesNotExistException()
        query = models.BookCarriers.insert().values(
            book_id=book.id, user_id=user.id, return_date=form.return_date)
        db.execute(query)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.put('/change_return_date/{relation_id}')
async def change_return_date(
        current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
        relation_id: int,
        form: Annotated[book_schemes.ChangeReturnDateForm, fastapi.Depends()],
        db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        relation = db.query(models.BookCarriers)\
            .filter(models.BookCarriers.c.id == relation_id).first()
        if not relation:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='Relationship doesn\'t exist!'
            )
        query = models.BookCarriers.update().where(
            models.BookCarriers.c.id == relation_id
        ).values(return_date=form.return_date)
        db.execute(query)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.delete('/remove_book_relation/{relation_id}')
async def remove_book_relation(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    relation_id: int,
    db: Session = fastapi.Depends(get_db)
):
    if await core.validators.is_librarian(current_user):
        relation = db.query(models.BookCarriers)\
            .filter(models.BookCarriers.c.id == relation_id).first()
        if not relation:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='Relationship doesn\'t exist!'
            )
        query = models.BookCarriers.delete().where(
            models.BookCarriers.c.id == relation_id
        )
        db.execute(query)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.get('/user/{user_id}', response_model=book_schemes.BookListForm)
async def get_user_books(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                         user_id: int,
                         db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise core.exceptions.UserDoesNotExistException()
        result = book_schemes.BookListForm(books=[])
        for book in user.books:
            result.books.append(book_schemes.ShortBookForm(
                id=book.id,
                title=book.title,
                authors=book.authors,
                edition_date=book.edition_date,
            ))
        return result

    raise core.exceptions.NotEnoughRightsException()


@router.post('/search/{page}')
async def search_book(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      #   form: Annotated[book_schemes.SearchBookForm, fastapi.Depends()],
                      query: str,
                      page: int,
                      edition_date: Optional[int] = None,
                      db: Session = fastapi.Depends(get_db)
                      ):
    ids = BookSearchCRUD().search(query)
    book_query = db.query(models.Book)
    if ids:
        book_query = book_query.filter(models.Book.id.in_(ids))
        if edition_date:
            book_query = book_query.filter(models.Book.edition_date == edition_date)

        if not await core.validators.is_librarian(current_user):
            book_query = book_query.filter(models.Book.is_private == False)  # noqa
    else:
        book_query = book_query.filter(False)

    return paginate(page, book_query, converter_book_scheme)


@router.post('/load_csv')
async def load_books(csv_file: fastapi.UploadFile,
                     current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                     images: List[fastapi.UploadFile] = fastapi.File(None, media_type='image/png'),
                     db: Session = fastapi.Depends(get_db)):
    """ File format (.csv):
        delimiter = ";"
        Columns (only in this order!):
        ___
        Title | Authors | Description | Amount | Edition date (year) | image (filename)
    """
    if await core.validators.is_librarian(current_user):
        try:
            await handle_csv(file=csv_file, handle_func=handle_books, db=db, images=images)
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.get('/books_csv')
async def get_books_csv(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    background_tasks: fastapi.BackgroundTasks,
    db: Session = fastapi.Depends(get_db),
):
    """ Out file format:
    ___
    Title | Authors | Description | Amount | Edition date (year) | image (filename)
    """
    if await core.validators.is_librarian(current_user):
        books = db.query(models.Book).all()
        header = ['Title',  'Authors', 'Description', 'Amount', 'Edition date', 'image']
        try:
            path = await write_to_csv(books, book_write_func, header)
            background_tasks.add_task(remove_file, path)
            return fastapi.responses.FileResponse(path, media_type='text/csv')

        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.get('/test')
async def test(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    query: str
):
    tokens = query.split()
    clauses = [
        {
            'span_multi': {
                'match': {'fuzzy': {"name": {'value': token, 'fuzziness': 'AUTO'}}}
            }
        }
        for token in tokens
    ]
    payload = {
        'bool': {
            'must': [{'span_near': {'clauses': clauses, 'slop': 0, 'in_order': False}}]
        }
    }
    resp = es.search(index='', query=payload, size=10)
    return [result['_source']['name'] for result in resp['hits']['hits']]

