import pydantic
import datetime as dt
import typing
from models import Rights


class User(pydantic.BaseModel):
    name: str
    middlename: str
    surname: str
    year_of_study: int
    birthdate: dt.date
    rights: Rights

    @pydantic.field_validator('year_of_study')
    @classmethod
    def validate_year(cls, value):
        assert 1 <= value <= 11
        return value


class CreateUsersRequestModel(pydantic.BaseModel):
    users: typing.List[User]


class UserResponseModel(pydantic.BaseModel):
    name: str
    middlename: str
    surname: str
    login: str
    password: str


class CreateUsersResponseModel(pydantic.BaseModel):
    users: typing.List[UserResponseModel]


class TokenResponseModel(pydantic.BaseModel):
    access_token: str
    token_type: str
