import sqlalchemy
from models import Base

engine = sqlalchemy.create_engine(
    'sqlite:///./test.db', connect_args={'check_same_thread': False}
)

Base.metadata.create_all(bind=engine)

SessionLocal = sqlalchemy.orm.sessionmaker(autoflush=False, bind=engine)


def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()
