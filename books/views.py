import fastapi
from core.db import get_db
import models
import core.exceptions
import core.validators
from . import schemes as book_schemes
from typing import Annotated
from auth.utils import get_current_user
from sqlalchemy.orm import Session

router = fastapi.APIRouter()


@router.get('/{book_id}', response_model=book_schemes.BookResponseModel)
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
        is_private=book.is_private
    )


@router.post('/create_book')
async def create_book(current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      form: Annotated[book_schemes.BookCreateRequestForm, fastapi.Depends()],
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        book = models.Book(
            title=form.title,
            authors=form.authors,
            description=form.description,
            edition_date=form.edition_date,
            is_private=form.is_private,
            amount=form.amount
        )
        db.add(book)
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()


@router.put('/edit/{book_id}')
async def edit_book(book_id: int,
                    current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                    form: Annotated[book_schemes.BookCreateRequestForm, fastapi.Depends()],
                    db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        book = db.query(models.Book).filter(models.Book.id == book_id).first()
        if book is None:
            raise core.exceptions.BookDoesNotExistException()
        book.title = form.title
        book.description = form.description
        book.amount = form.amount
        book.authors = form.authors
        book.is_private = form.is_private
        book.edition_date = form.edition_date

        db.add(book)
        db.commit()
        return fastapi.status.HTTP_200_OK
    raise core.exceptions.NotEnoughRightsException()


@router.delete('/delete/{book_id}')
async def delete_book(book_id: int,
                      current_user: Annotated[models.User, fastapi.Depends(get_current_user)],
                      db: Session = fastapi.Depends(get_db)):
    if await core.validators.is_librarian(current_user):
        book = db.query(models.Book).filter(models.Book.id == book_id)
        if book.first() is None:
            raise core.exceptions.BookDoesNotExistException()
        if len(book.first().owners) != 0:
            raise fastapi.exceptions.HTTPException(
                status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail='Book has owners!'
            )
        book.delete()
        db.commit()
        return fastapi.status.HTTP_200_OK

    raise core.exceptions.NotEnoughRightsException()
