import sqlalchemy
from models import Base

engine = sqlalchemy.create_engine(
    'sqlite:///./app.db', connect_args={'check_same_thread': False}
)

Base.metadata.create_all(bind=engine)

SessionLocal = sqlalchemy.orm.sessionmaker(autoflush=False, bind=engine)
db = SessionLocal()
