from main import app
from fastapi.testclient import TestClient
import pytest
from core.security import get_password_hash
from models import User, Rights
from core.test_db import Base, engine, override_get_db
from core.db import get_db
import datetime as dt
from core.search.cruds import UserCRUD

app.dependency_overrides[get_db] = override_get_db
db = next(override_get_db())

client = TestClient(app)


@pytest.fixture()
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    for user in db.query(User).all():
        UserCRUD().delete(user.id)
    Base.metadata.drop_all(bind=engine)


def create_student():
    login = 'test'
    password = 'pwd123qwe'
    user = User(login=login, password=get_password_hash(password),
                rights=Rights.student)
    db.add(user)
    db.commit()
    return [
        login,
        password,
        user
    ]


def create_admin():
    admin_login = 'admin'
    admin_password = 'pwd123qwe'
    admin = User(login=admin_login, password=get_password_hash(admin_password),
                 rights=Rights.admin)
    db.add(admin)
    db.commit()
    return [
        admin_login,
        admin_password,
        admin
    ]


def test_get_user(test_db):
    login, password, user = create_student()

    resp = client.get(f'/users/info/{user.id}')
    assert resp.status_code == 401

    admin_login, admin_password, admin = create_admin()
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }

    resp = client.post('/auth/login', headers=headers, data=data)

    r1 = client.get(f'/users/info/{user.id}', headers=resp.headers)
    r2 = client.get(f'/users/info/{admin.id}', headers=resp.headers)

    assert r1.status_code == 200
    assert r2.status_code == 403

    data = {
        'username': admin_login,
        'password': admin_password
    }
    resp = client.post('/auth/login', headers=headers, data=data)
    r1 = client.get(f'/users/info/{user.id}', headers=resp.headers)
    r2 = client.get(f'/users/info/{admin.id}', headers=resp.headers)

    assert r1.status_code == 200
    assert r2.status_code == 200


def test_edit_user(test_db):
    login, password, user = create_student()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    resp = client.post('/auth/login', headers=headers, data=data)

    form_data = {
        'name': 'string',
        'middlename': 'string',
        'surname': 'string',
        'year_of_study': 10,
        'birthdate': '2024-07-07',
        'rights': Rights.admin.value
    }

    edit_resp = client.put(f'/users/edit/{user.id}', headers=resp.headers, params=form_data)
    assert edit_resp.status_code == 403

    admin_login, admin_password, _ = create_admin()
    data = {
        'username': admin_login,
        'password': admin_password
    }
    resp = client.post('/auth/login', headers=headers, data=data)

    headers.update(dict(resp.headers))
    edit_resp = client.put(f'/users/edit/{user.id}', headers=headers, params=form_data)
    assert edit_resp.status_code == 200

    db.refresh(user)
    user_result = user.__dict__
    user_result['rights'] = user_result['rights'].value
    form_data['birthdate'] = dt.date.fromisoformat(form_data['birthdate'])
    for key, value in form_data.items():
        assert user_result[key] == value


def test_delete_user(test_db):
    login, password, user = create_student()
    admin_login, admin_password, admin = create_admin()

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {
        'username': login,
        'password': password
    }
    resp = client.post('/auth/login', headers=headers, data=data)
    r1 = client.delete(f'/users/delete/{user.id}', headers=resp.headers)
    assert r1.status_code == 403

    data['username'] = admin_login
    data['password'] = admin_password
    resp = client.post('/auth/login', headers=headers, data=data)
    r2 = client.delete(f'/users/delete/{user.id}', headers=resp.headers)
    assert r2.status_code == 200
    assert len(db.query(User).all()) == 1
