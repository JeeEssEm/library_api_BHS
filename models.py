import sqlalchemy.orm
import sqlalchemy
import enum


class Rights(enum.IntEnum):
    admin = 2
    librarian = 1
    student = 0


class Base(sqlalchemy.orm.DeclarativeBase):
    pass


BookCarriers = sqlalchemy.Table(
    'BookCarriers',
    Base.metadata,
    sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True,
                      index=True, autoincrement=True, nullable=False),
    sqlalchemy.Column('book_id',
                      sqlalchemy.Integer, sqlalchemy.ForeignKey('Book.id')),
    sqlalchemy.Column('user_id',
                      sqlalchemy.Integer, sqlalchemy.ForeignKey('User.id')),
    sqlalchemy.Column('return_date', sqlalchemy.Date),
)


class Book(Base):
    __tablename__ = 'Book'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           index=True, autoincrement=True, nullable=False)
    title = sqlalchemy.Column(sqlalchemy.String)
    authors = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.Text)
    edition_date = sqlalchemy.Column(sqlalchemy.Integer)
    amount = sqlalchemy.Column(sqlalchemy.Integer)
    is_private = sqlalchemy.Column(sqlalchemy.Boolean)
    image = sqlalchemy.Column(sqlalchemy.String)

    owners = sqlalchemy.orm.relationship('User', secondary=BookCarriers)


class User(Base):
    __tablename__ = 'User'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True,
                           index=True, autoincrement=True, nullable=False)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=False, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    name = sqlalchemy.Column(sqlalchemy.VARCHAR(32))
    middlename = sqlalchemy.Column(sqlalchemy.VARCHAR(32))
    surname = sqlalchemy.Column(sqlalchemy.VARCHAR(32))
    birthdate = sqlalchemy.Column(sqlalchemy.Date)
    year_of_study = sqlalchemy.Column(sqlalchemy.Integer)
    rights = sqlalchemy.Column(sqlalchemy.Enum(Rights))

    books = sqlalchemy.orm.relationship('Book', secondary=BookCarriers)
