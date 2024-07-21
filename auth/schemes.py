import pydantic
import datetime as dt
import typing
from models import Rights


class User(pydantic.BaseModel):
    name: typing.Optional[str] = pydantic.Field(None, description='Name')
    middlename: typing.Optional[str] = pydantic.Field(None, description='Middle name')
    surname: typing.Optional[str] = pydantic.Field(None, description='Surname')
    year_of_study: typing.Optional[int] = pydantic.Field(
        None, description='Current year of study (class)')
    birthdate: typing.Optional[dt.date] = pydantic.Field(None, description='Birth date')
    rights: typing.Optional[Rights] = pydantic.Field(
        None, description='Rights (admin/librarian/student)')

    @pydantic.field_validator('year_of_study')
    @classmethod
    def validate_year(cls, value):
        if value:
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


class ChangePasswordRequestForm(pydantic.BaseModel):
    new_password: str


class WhoamiResponseModel(pydantic.BaseModel):
    login: str
    name: str
    middlename: str
    surname: str
    year_of_study: int
    birthdate: dt.date
    rights: Rights
