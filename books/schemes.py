import pydantic
import typing
from fastapi import UploadFile


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
