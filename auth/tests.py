from main import app
from fastapi.testclient import TestClient
import pytest
from core.security import get_password_hash, generate_token, create_tokens
import datetime as dt
from models import User, Rights
from core.test_db import Base, engine, override_get_db
from core.db import get_db
from core.search.cruds import UserCRUD

client = TestClient(app)
app.dependency_overrides[get_db] = override_get_db
db = next(override_get_db())


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    for user in db.query(User).all():
        UserCRUD().delete(user.id)

    Base.metadata.drop_all(bind=engine)


def test_unauth():
    resp = client.get('/auth/whoami')
    assert resp.status_code == 401


def test_login(test_db):
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password))
    db.add(user)
    db.commit()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    resp = client.post('/auth/login', data=data, headers=headers)
    assert resp.status_code == 200  # all credentials are correct

    data['password'] += '1'
    resp = client.post('/auth/login', data=data, headers=headers)
    assert resp.status_code == 401  # wrong password

    data['password'] = data['password'][:-1]
    data['username'] += '1'
    resp = client.post('/auth/login', data=data, headers=headers)
    assert resp.status_code == 401  # wrong login


def test_get_current_user(test_db):
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password))
    db.add(user)
    db.commit()

    resp = client.get('/auth/whoami')
    assert resp.status_code == 401

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    resp = client.post('/auth/login', data=data, headers=headers)
    resp = client.get('/auth/whoami', headers={
        'Authorization': resp.headers['Authorization']
    })
    assert resp.status_code == 200


def test_expired_access_token(test_db):
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password))
    db.add(user)
    db.commit()

    expired_access_token = generate_token(
        user.id, dt.datetime.now().timestamp() - 1)
    resp = client.get('/auth/whoami', headers={
        'Authorization': f'Bearer {expired_access_token}'
    })
    assert resp.status_code == 401

    valid_access_token = generate_token(
        user.id, dt.datetime.now().timestamp() + 1000)
    resp = client.get('/auth/whoami', headers={
        'Authorization': f'Bearer {valid_access_token}'
    })
    assert resp.status_code == 200


def test_update_token(test_db):
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password))
    db.add(user)
    db.commit()

    resp = client.post('/auth/update_token', headers={'Cookie': ''})
    assert resp.status_code == 401  # empty refresh token

    resp = client.post('/auth/update_token', headers={'Cookie': 'asd123sdafsd'})
    assert resp.status_code == 401  # invalid refresh token

    expired_refresh_token = generate_token(user.id, dt.datetime.now().timestamp() - 1)
    resp = client.post('/auth/update_token', headers={
        'Cookie': f'refresh_token={expired_refresh_token}'}
    )
    assert resp.status_code == 401  # expired refresh token

    tokens = create_tokens(user.id)
    resp = client.post('/auth/update_token', headers={
        'Cookie': f'refresh_token={tokens["refresh_token"]}'
    })
    assert resp.status_code == 200  # valid refresh token


def test_create_users(test_db):
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password),
                rights=Rights.student)
    db.add(user)
    db.commit()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    resp = client.post('/auth/login', data=data, headers=headers)
    input_data = {
        'users': [
            {
                'name': 'Иван',
                'middlename': 'Иваныч',
                'surname': 'Иванов',
                'year_of_study': 11,
                'birthdate': '2006-04-02',
                'rights': Rights.student.value
            },
            {
                'name': 'Акакий',
                'middlename': 'Матвеевич',
                'surname': 'Братишкин',
                'year_of_study': 11,
                'birthdate': '2006-05-03',
                'rights': Rights.student.value
            }
        ]
    }
    headers = {
        'Authorization': resp.headers['Authorization']
    }
    resp = client.post('/auth/create', json=input_data, headers=headers)
    assert resp.status_code == 403

    user.rights = Rights.librarian
    db.add(user)
    db.commit()

    resp = client.post('/auth/create', json=input_data, headers=headers)
    assert resp.status_code == 403

    user.rights = Rights.admin
    db.add(user)
    db.commit()

    resp = client.post('/auth/create', json=input_data, headers=headers)
    assert resp.status_code == 200

    data = resp.json()['users']
    logins = [data[0]['login'], data[1]['login']]

    students = db.query(User).filter(User.login.in_(logins)).all()
    assert len(students) == 2
