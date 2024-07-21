import pydantic
import typing


class BookResponseModel(pydantic.BaseModel):
    title: str
    authors: str
    description: str
    edition_date: int
    in_stock: int
    is_private: typing.Optional[bool] = None
    # TODO: image


class BookCreateRequestForm(pydantic.BaseModel):
    title: str
    authors: str
    description: str
    edition_date: int
    amount: int
    is_private: bool
    # TODO: image
