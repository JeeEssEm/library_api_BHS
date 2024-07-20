from passlib.context import CryptContext
import secrets
from main import (PASSWORD_LENGTH, SECRET_KEY, REFRESH_TOKEN_EXPIRES,
                  ACCESS_TOKEN_EXPIRES)
import datetime as dt
import jwt

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
ALGORITHM = 'HS256'


def generate_random_password():
    return secrets.token_urlsafe(PASSWORD_LENGTH)


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(pwd, hashed_pwd):
    return pwd_context.verify(pwd, hashed_pwd)


def generate_login(id_):
    return 'sch' + dt.datetime.utcnow().strftime('%Y') + str(id_)


def create_tokens(user_id):
    access_token = jwt.encode(
        {
            'id': user_id,
            'exp': dt.datetime.utcnow() + dt.timedelta(
                minutes=ACCESS_TOKEN_EXPIRES
            )
        },
        algorithm=ALGORITHM,
        key=SECRET_KEY
    )
    refresh_token = jwt.encode(
        {
            'id': user_id,
            'exp': dt.datetime.utcnow() + dt.timedelta(
                days=REFRESH_TOKEN_EXPIRES
            )
        },
        algorithm=ALGORITHM,
        key=SECRET_KEY
    )

    return {
        'access_token': access_token,
        'refresh_token': refresh_token
    }


def decode_token(token):
    return jwt.decode(
        token, algorithms=[ALGORITHM],
        key=SECRET_KEY, verify=False
    )


def is_valid_token(token):
    try:
        token = decode_token(token)
        return True
    except Exception:
        return False
