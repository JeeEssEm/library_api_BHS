from dotenv import load_dotenv
import os
import pathlib

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ.get('DB_URL', default='sqlite:///./app.db')
PASSWORD_LENGTH = int(os.environ.get('PASSWORD_LENGTH', default=8))
SECRET_KEY = os.environ.get('SECRET_KEY', default='NOT SECRET!')
REFRESH_TOKEN_EXPIRES = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS',
                                           default=30))
ACCESS_TOKEN_EXPIRES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES',
                                          default=30))
ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', default=10))
STATIC_PATH = pathlib.Path(__file__).resolve().parent / os.environ.get('STATIC_PATH',
                                                                       default='static')
SEARCHER_PATH = pathlib.Path(__file__).resolve().parent / os.environ.get('SEARCHER_PATH',
                                                                         default='static')
