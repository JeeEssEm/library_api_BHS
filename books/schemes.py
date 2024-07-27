import pydantic
import typing
from fastapi import UploadFile
import datetime as dt


class BookResponseModel(pydantic.BaseModel):
    title: str
    authors: str
    description: str
    edition_date: int
    in_stock: int
    is_private: typing.Optional[bool] = None


class BookCreateRequestForm(pydantic.BaseModel):
    title: str
    authors: str
    description: str
    edition_date: int
    amount: int
    is_private: bool
    image: typing.Optional[UploadFile] = None


class BookEditRequestForm(pydantic.BaseModel):
    title: typing.Optional[str] = None
    authors: typing.Optional[str] = None
    description: typing.Optional[str] = None
    edition_date: typing.Optional[int] = None
    amount: typing.Optional[int] = None
    is_private: typing.Optional[bool] = None
    image: typing.Optional[UploadFile] = None


class GiveReturnBookForm(pydantic.BaseModel):
    user_id: int
    book_id: int
    return_date: dt.date


class ChangeReturnDateForm(pydantic.BaseModel):
    return_date: dt.date


class ShortBookForm(pydantic.BaseModel):
    id: int
    title: str
    authors: str
    edition_date: int


class BookListForm(pydantic.BaseModel):
    books: typing.List[ShortBookForm]


class SearchBookForm(pydantic.BaseModel):
    title: typing.Optional[str] = None
    authors: typing.Optional[str] = None
    edition_date: typing.Optional[int] = None


class ReturnDateForm(pydantic.BaseModel):
    return_date: dt.date


class DebtorBookForm(pydantic.BaseModel):
    id: int
    title: str
    authors: str
    edition_date: int
    return_date: dt.date


class DebtorForm(pydantic.BaseModel):
    id: int
    name: str
    surname: str
    middlename: str
    year_of_study: int

    expired_books: typing.List[DebtorBookForm]


class DebtorsListForm(pydantic.BaseModel):
    debtors: typing.List[DebtorForm]
