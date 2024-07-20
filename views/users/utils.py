from main import db
import fastapi
from typing import Annotated
import core.security
import models
import jwt

oauth2_scheme = fastapi.security.OAuth2PasswordBearer(tokenUrl='users/login')


async def get_current_user(token:
                           Annotated[str, fastapi.Depends(oauth2_scheme)]):
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
