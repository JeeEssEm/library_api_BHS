from core.db import get_db
from models import Rights, User
from getpass import getpass
from core.security import get_password_hash


db = list(get_db())[0]


def main():
    print('Create superuser!')
    login = input('Enter user login: ')
    password = getpass('Enter user password: ')
    repeat_password = getpass('Repeat user password: ')

    if password != repeat_password:
        print('Passwords are different! Restart program to continue...')
        return
    if len(db.query(User).filter(User.login == login).all()) != 0:
        print('User with this login already exists! Restart program to continue...')
        return

    try:
        user = User(login=login, password=get_password_hash(password),
                    rights=Rights.admin)
        db.add(user)
        db.commit()
        print('Superuser created successfully!')
    except Exception as exc:
        print(f'Something went wrong! Error: {exc}')


if __name__ == '__main__':
    main()
