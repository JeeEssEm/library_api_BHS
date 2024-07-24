import fastapi
from typing import Annotated
import core.security
import models
import jwt
from sqlalchemy.orm import Session
from core.db import get_db

oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl='auth/login')


async def get_current_user(
        token:
        Annotated[str, fastapi.Depends(oauth2_scheme)],
        db: Annotated[Session, fastapi.Depends(get_db)]):
    try:
        data = core.security.decode_token(token)
        user = db.query(models.User).filter(
            models.User.id == data.get('id')).first()
        return user
    except jwt.exceptions.ExpiredSignatureError:
        raise fastapi.exceptions.HTTPException(
            status_code=fastapi.status.HTTP_401_UNAUTHORIZED,
            detail='Token expired'
        )


async def is_authenticated(request: fastapi.Request):
    return request.headers.get('Authorization') is not None
