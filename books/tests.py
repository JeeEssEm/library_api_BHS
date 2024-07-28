from main import app
from fastapi.testclient import TestClient
import pytest
from core.security import get_password_hash
from models import User, Rights, Book, BookCarriers
from core.test_db import Base, engine, override_get_db
from core.db import get_db
import datetime as dt
from core.search.cruds import UserCRUD, BookCRUD
import enum
from PIL import Image
from io import BytesIO


class MethodsEnum(enum.Enum):
    get = 'get'
    post = 'post'
    put = 'put'
    delete = 'delete'


app.dependency_overrides[get_db] = override_get_db
db = next(override_get_db())

client = TestClient(app)


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    for user in db.query(User).all():
        UserCRUD().delete(user.id)
    for book in db.query(Book).all():
        BookCRUD().delete(book.id)
    Base.metadata.drop_all(bind=engine)


def create_user(login: str, password: str, rights: Rights):
    user = User(login=login, password=get_password_hash(password),
                rights=rights)
    db.add(user)
    db.commit()
    return user


def sign_in(login, password):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    return client.post('/auth/login', headers=headers, data=data)


def create_book(title, description=None, authors=None, edition_date=2024,
                amount=100, is_private=False, image=None):
    if not description:
        description = 'Какое-то описание'
    if not authors:
        authors = 'Ну кто-то же написал эту книгу'

    if image is None:
        image = ''
    data = {
        'title': title,
        'description': description,
        'authors': authors,
        'edition_date': edition_date,
        'amount': amount,
        'is_private': is_private,
    }
    files = {}
    if image:
        files = {'files': ('image', image, 'image/webp')}

    book = send_request(
        '/books/create_book',
        MethodsEnum.post,
        Rights.admin,
        headers={'Content-Type': 'Content-Type: multipart/form-data'},
        files=files,
        params=data
    ).json()
    book_model = db.query(Book).filter(Book.id == book['id']).first()
    return book_model


def send_request(url: str, method: MethodsEnum, user_rights: Rights,
                 login=None, password=None, **kwargs):
    methods = {
        MethodsEnum.get: client.get,
        MethodsEnum.post: client.post,
        MethodsEnum.put: client.put,
        MethodsEnum.delete: client.delete
    }
    if not login or not password:
        login = 'access_test'
        password = 'hashed_pass'
        q = db.query(User).filter(User.login == login)
        user = q.first()
        if user is None:
            user = create_user(login, password, rights=user_rights)
        else:
            user.rights = user_rights
        db.add(user)
        db.commit()

    resp_login = sign_in(login, password)
    if kwargs.get('headers'):
        kwargs['headers']['Authorization'] = resp_login.headers['Authorization']
    else:
        kwargs['headers'] = {'Authorization': resp_login.headers['Authorization']}
    return methods[method](url, **kwargs)


def test_book_info(test_db):
    public_book = create_book('public_book', is_private=False)
    private_book = create_book('private_book', is_private=True)

    student_public_resp = send_request(
        f'/books/info/{public_book.id}',
        MethodsEnum.get,
        Rights.student
    )
    assert student_public_resp.status_code == 200
    assert student_public_resp.json()['title'] == 'public_book'

    student_private_resp = send_request(
        f'/books/info/{private_book.id}',
        MethodsEnum.get,
        Rights.student
    )
    assert student_private_resp.status_code == 404

    lib_private_resp = send_request(
        f'/books/info/{private_book.id}',
        MethodsEnum.get,
        Rights.librarian
    )
    assert lib_private_resp.status_code == 200
    assert lib_private_resp.json()['title'] == 'private_book'

    lib_404_resp = send_request(
        '/books/info/123123123',
        MethodsEnum.get,
        Rights.librarian
    )
    assert lib_404_resp.status_code == 404


def test_media(test_db):
    img = Image.new('RGB', (256, 144), (255, 255, 255))
    storage = BytesIO()
    img.save(storage, 'webp')
    storage.seek(0)

    book = create_book('book with image', image=storage.getvalue())

    # assert book.image != None # TODO: доделать проверку на сохранение изображений

    resp = send_request(f'/books/media/{book.id}', MethodsEnum.get, Rights.admin)
    assert resp.status_code == 200


def test_create(test_db):
    data = {
        'title': 'title',
        'description': 'description',
        'authors': 'authors',
        'edition_date': 123,
        'amount': 123,
        'is_private': False,
    }
    count_books = db.query(Book).count()
    resp = send_request(
        '/books/create_book',
        MethodsEnum.post,
        Rights.student,
        headers={'Content-Type': 'Content-Type: multipart/form-data'},
        params=data
    )
    assert resp.status_code == 403
    assert db.query(Book).count() == count_books

    resp = send_request(
        '/books/create_book',
        MethodsEnum.post,
        Rights.librarian,
        headers={'Content-Type': 'Content-Type: multipart/form-data'},
        params=data
    )
    assert resp.status_code == 200
    assert db.query(Book).count() == count_books + 1


def test_edit(test_db):
    book = create_book('editable book')

    resp = send_request(
        f'/books/edit/{book.id}',
        MethodsEnum.put,
        Rights.student,
        params={
            'title': 'edited book'
        }
    )
    assert resp.status_code == 403
    assert book.title == 'editable book'

    resp = send_request(
        f'/books/edit/{book.id}',
        MethodsEnum.put,
        Rights.librarian,
        params={
            'title': 'edited book'
        }
    )
    assert resp.status_code == 200
    assert book.title == 'edited book'


def test_delete(test_db):
    book = create_book('still alive')
    book_count = db.query(Book).count()

    resp = send_request(
        f'/books/delete/{book.id}',
        MethodsEnum.delete,
        Rights.student
    )
    assert resp.status_code == 403
    assert db.query(Book).count() == book_count

    resp = send_request(
        f'/books/delete/{book.id}',
        MethodsEnum.delete,
        Rights.librarian
    )
    assert resp.status_code == 200
    assert db.query(Book).count() == book_count - 1


def test_relations(test_db):
    book = create_book('I am a book!')

    login, password = 'just_user', 'just_password'
    user = create_user(login, password, Rights.student)

    data = {
        'user_id': user.id,
        'book_id': book.id,
        'return_date': str(dt.date(2024, 8, 28))
    }
    resp = send_request(
        '/books/give_book',
        MethodsEnum.post,
        Rights.student,
        params=data
    )
    assert resp.status_code == 403

    resp = send_request(
        '/books/give_book',
        MethodsEnum.post,
        Rights.librarian,
        params=data
    )
    assert resp.status_code == 200
    rel = db.query(BookCarriers)\
            .filter(BookCarriers.c.book_id == book.id)\
            .filter(BookCarriers.c.user_id == user.id)\
            .filter(BookCarriers.c.return_date == data['return_date']).first()
    assert rel is not None
    assert str(rel.return_date) == data['return_date']

    # edit return date
    data['return_date'] = str(dt.date(2023, 7, 27))
    resp = send_request(
        '/books/change_return_date',
        MethodsEnum.put,
        Rights.librarian,
        params=data
    )
    rel = db.query(BookCarriers)\
            .filter(BookCarriers.c.book_id == book.id)\
            .filter(BookCarriers.c.user_id == user.id)\
            .filter(BookCarriers.c.return_date == data['return_date']).first()
    assert str(rel.return_date) == data['return_date']

    # get return date
    resp = send_request(
        '/books/return_date',
        MethodsEnum.get,
        Rights.student,
        login=login, password=password,
        params={'user_id': data['user_id'], 'book_id': data['book_id']}
    )
    assert resp.status_code == 200
    assert resp.json()['return_date'] == data['return_date']

    resp = send_request(
        '/books/return_date',
        MethodsEnum.get,
        Rights.student,
        params={'user_id': data['user_id'], 'book_id': data['book_id']}
    )
    assert resp.status_code == 403

    resp = send_request(
        '/books/return_date',
        MethodsEnum.get,
        Rights.librarian,
        params={'user_id': data['user_id'], 'book_id': data['book_id']}
    )
    assert resp.status_code == 200

    # delete return date
    count_relations = db.query(BookCarriers).count()
    resp = send_request(
        '/books/remove_book_relation',
        MethodsEnum.delete,
        Rights.student,
        login=login, password=password,
        params={'user_id': data['user_id'], 'book_id': data['book_id']}
    )
    assert resp.status_code == 403
    assert count_relations == db.query(BookCarriers).count()

    resp = send_request(
        '/books/remove_book_relation',
        MethodsEnum.delete,
        Rights.librarian,
        params={'user_id': data['user_id'], 'book_id': data['book_id']}
    )
    assert resp.status_code == 200
    assert count_relations - 1 == db.query(BookCarriers).count()


def test_get_user_books(test_db):
    books = [create_book('book 1'), create_book('book 2')]

    creds = [('user 1', 'pwd1'), ('user 2', 'pwd2')]
    users = [create_user(login, password, Rights.student) for login, password in creds]

    resp = send_request(
        '/books/give_book', MethodsEnum.post, Rights.librarian,
        params={
            'user_id': users[0].id,
            'book_id': books[0].id,
            'return_date': str(dt.date(2023, 7, 7))
        }
    )
    assert resp.status_code == 200
    resp = send_request(
        '/books/give_book', MethodsEnum.post, Rights.librarian,
        params={
            'user_id': users[0].id,
            'book_id': books[1].id,
            'return_date': str(dt.date(2023, 7, 7))
        }
    )
    assert resp.status_code == 200

    resp = send_request(
        '/books/give_book', MethodsEnum.post, Rights.librarian,
        params={
            'user_id': users[1].id,
            'book_id': books[0].id,
            'return_date': str(dt.date(2024, 7, 7))
        }
    )
    assert resp.status_code == 200

    resp = send_request(
        f'/books/user/{users[0].id}', MethodsEnum.get, Rights.student,
        login=creds[0][0], password=creds[0][1]
    )
    assert resp.status_code == 200
    assert len(resp.json()['books']) == 2

    resp = send_request(
        f'/books/user/{users[1].id}', MethodsEnum.get, Rights.librarian,
    )
    assert resp.status_code == 200
    assert len(resp.json()['books']) == 1

    resp = send_request(
        f'/books/user/{users[1].id}', MethodsEnum.get, Rights.student,
    )
    assert resp.status_code == 403

    # get debtors
    resp = send_request(
        '/books/debtors', MethodsEnum.get, Rights.librarian
    )
    assert resp.status_code == 200
    assert len(resp.json()['debtors']) == 2

    resp = send_request(
        '/books/debtors', MethodsEnum.get, Rights.librarian,
        params={'return_date': str(dt.date(2024, 1, 1))}
    )
    assert resp.status_code == 200
    assert len(resp.json()['debtors']) == 1
