import sqlalchemy
from config import SQLALCHEMY_DATABASE_URL
from models import Base

engine = sqlalchemy.create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
)

Base.metadata.create_all(bind=engine)


def get_db():
    SessionLocal = sqlalchemy.orm.sessionmaker(autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
