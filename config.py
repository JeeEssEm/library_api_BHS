from dotenv import load_dotenv
import os

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ.get('DB_URL')
PASSWORD_LENGTH = int(os.environ.get('PASSWORD_LENGTH', default=8))
SECRET_KEY = os.environ.get('SECRET_KEY', default='NOT SECRET!')
REFRESH_TOKEN_EXPIRES = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS',
                                           default=30))
ACCESS_TOKEN_EXPIRES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES',
                                          default=30))
ITEMS_PER_PAGE = int(os.environ.get('ITEMS_PER_PAGE', default=10))
