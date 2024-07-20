from views.users.views import router as users_router
from models import Base
import fastapi
from dotenv import load_dotenv
import os
import sqlalchemy

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.environ.get('DB_URL')
PASSWORD_LENGTH = int(os.environ.get('PASSWORD_LENGTH', default=8))
SECRET_KEY = os.environ.get('SECRET_KEY', default='NOT SECRET!')
REFRESH_TOKEN_EXPIRES = int(os.environ.get('REFRESH_TOKEN_EXPIRE_DAYS',
                                           default=30))
ACCESS_TOKEN_EXPIRES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES',
                                          default=30))


engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)

Base.metadata.create_all(bind=engine)

SessionLocal = sqlalchemy.orm.sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()

app = fastapi.FastAPI()

app.include_router(users_router, prefix='/users')
