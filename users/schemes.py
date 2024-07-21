import pydantic
import typing
import models


T = typing.TypeVar('T')


class UserSearch(pydantic.BaseModel):
    id: int
    name: str
    surname: str
    middlename: str
    rights: models.Rights


class PageResponseModel(pydantic.BaseModel, typing.Generic[T]):
    total: int
    page: int
    results: typing.List[T]
