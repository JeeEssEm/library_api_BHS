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


@router.get(
    '/info/{book_id}',
    response_model=book_schemes.BookResponseModel,
    description='''
## Get information about book
**Note:**
- only _admin_ or _librarian_ can access to private books
- only authenticated user can get public (not private) book
    ''')
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


@router.get(
    '/media/{book_id}',
    response_class=fastapi.responses.FileResponse,
    summary='Get book image',
    description='''
## Get book image (file)
**Note:** if book does not has image you will get _not_found_img_    
'''
)
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


@router.post(
    '/create_book',
    description='''
## Create book
**Params:**
- _edition_date_ parameter is an integer (ex. 2022), which is year when book was published
- _amount_ parameter is integer, which describes amount of books of this type in library
    ''')
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
            'id': str(book.id),
            'title': book.title,
            'description': book.description,
            'authors': book.authors
        })

        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.put(
    '/edit/{book_id}',
    description='''
## Edit existing book in database
**Params:**
- _edition_date_ parameter is an integer (ex. 2022), which is year when book was published
- _amount_ parameter is integer, which describes amount of books of this type in library
''')
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

        BookSearchCRUD().update(book.id, {
            'title': book.title,
            'description': book.description,
            'authors': book.authors
        })

        db.add(book)
        db.commit()
        return fastapi.status.HTTP_200_OK
    raise core.exceptions.NotEnoughRightsException()


@router.delete(
    '/delete/{book_id}',
    description='''
## Delete book from database!
**Note:** you **can't** delete book if users, who have not returned book of this type, exists
    ''')
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


@router.post(
    '/give_book',
    description='''
## Give user to book (make him owner)
**Params:**
- set return date, when user must return book. Otherwise librarian can find this user in debtors. Librarian can change return date...
    ''')
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


@router.put(
    '/change_return_date/{relation_id}',
    description='''
**Params:**
- _return_date_ field can be only in this format: _"{year}-{month}-{day}"_ (ex. 2000-12-30)
    ''')
async def change_return_date(
        current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
        user_id: int,
        book_id: int,
        form: Annotated[book_schemes.ChangeReturnDateForm, fastapi.Depends()],
        db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        relation = db.query(models.BookCarriers)\
            .filter(models.BookCarriers.c.book_id == book_id)\
            .filter(models.BookCarriers.c.user_id == user_id).first()
        if not relation:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='Relationship doesn\'t exist!'
            )
        query = models.BookCarriers.update().where(
            models.BookCarriers.c.book_id == book_id and
            models.BookCarriers.c.user_id == user_id
        ).values(return_date=form.return_date)
        db.execute(query)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.delete(
    '/remove_book_relation/{relation_id}',
    description='''
## Delete relation between book and user!
I.e. user returns book to the library
    '''
)
async def remove_book_relation(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    user_id: int,
    book_id,
    db: Session = fastapi.Depends(get_db)
):
    if await core.validators.is_librarian(current_user):
        relation = db.query(models.BookCarriers)\
            .filter(models.BookCarriers.c.book_id == book_id)\
            .filter(models.BookCarriers.c.user_id == user_id).first()
        if not relation:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='Relationship doesn\'t exist!'
            )
        query = models.BookCarriers.delete().where(
            models.BookCarriers.c.book_id == book_id and
            models.BookCarriers.c.user_id == user_id
        )
        db.execute(query)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.get(
    '/user/{user_id}',
    response_model=book_schemes.BookListForm,
    description='''
## Get info about books, which user has
    '''
)
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


@router.get(
    '/return_date',
    response_model=book_schemes.ReturnDateForm,
    description='''
## Get return date of book
    '''
)
async def get_book_return_date(
    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
    user_id: int,
    book_id: int,
    db: Session = fastapi.Depends(get_db)
):
    if current_user.id != user_id or not await core.validators.is_librarian(current_user):
        relation = db.query(models.BookCarriers)\
            .filter(models.BookCarriers.c.book_id == book_id)\
            .filter(models.BookCarriers.c.user_id == user_id).first()
        if not relation:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_404_NOT_FOUND,
                detail='Relationship doesn\'t exist!'
            )
        return book_schemes.ReturnDateForm(return_date=relation.return_date)

    raise core.exceptions.NotEnoughRightsException()


@router.post(
    '/search/{page}',
    description='''
## Searches through indexed values and returns results by page
* You can set optional filter for _edition_date_ to filter books
* Empty _query_ parameter makes you get all books
    '''
)
async def search_book(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      page: int,
                      query: str = None,
                      edition_date: Optional[int] = None,
                      db: Session = fastapi.Depends(get_db)
                      ):
    ids = []

    if query:
        ids = list(map(lambda item: int(item['id']), BookSearchCRUD().search(query, page)))
    book_query = db.query(models.Book)
    if ids:
        book_query = book_query.filter(models.Book.id.in_(ids))
        if edition_date:
            book_query = book_query.filter(models.Book.edition_date == edition_date)
    elif not ids and query:
        book_query = book_query.filter(False)
    if not await core.validators.is_librarian(current_user):
        book_query = book_query.filter(models.Book.is_private == False)  # noqa

    return paginate(page, book_query, converter_book_scheme)


@router.post(
    '/load_csv',
    description='''
## Upload books from csv to database
File format (.csv) <br>
_delimiter = ";"_ <br>
**Columns (only in this order!):**

| Title | Authors | Description | Amount | Edition date (year) | image (filename) |
| ----- | ------- | ----------- | ------ | ------------------- | ---------------- |
| Guide | Jes     | nah         | 1      | 2024                | null             |
| ...   | ...     | ...         | ...    | ...                 | ...              |

**Note:**
- _edition_date_ field is an integer (ex. 2022), which is year when book was published
- _image_ field is field, which has filename of loaded image
    ''')
async def load_books(csv_file: fastapi.UploadFile,
                     current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                     images: List[fastapi.UploadFile] = fastapi.File(None, media_type='image/png'),
                     db: Session = fastapi.Depends(get_db)):

    if await core.validators.is_librarian(current_user):
        try:
            await handle_csv(file=csv_file, handle_func=handle_books, db=db, images=images)
            return fastapi.status.HTTP_200_OK
        except Exception as exc:
            raise core.exceptions.SomethingWentWrongException(exc)

    raise core.exceptions.NotEnoughRightsException()


@router.get(
    '/books_csv',
    description='''
## Get all books from database in csv format

**Out file example:**
| Title | Authors | Description | Amount | Edition date (year) | image (filename) |
| ----- | ------- | ----------- | ------ | ------------------- | ---------------- |
| Guide | Jes     | nah         | 1      | 2024                | null             |
| ...   | ...     | ...         | ...    | ...                 | ...              |
    ''')
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
