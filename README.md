# API для библиотеки
...

## Routes
### Работа с аккаунтом
- `POST("/users/login")`
 INPUT: {"login": …, "password": …}
 OUTPUT: {"refresh_token": …, "access_token": …}
- `POST("/users/refresh_access_token")`
INPUT: {"refresh_token": …}
OUTPUT: {"access_token": …}
- `POST("/users/create")`
 Validators: is_admin
 INPUT: [{"name": …, "surname": …, "middlename": …, "birth": …, "year_of_study": …}, …] || .csv?
 OUTPUT: [{"name": …, "surname": …, "middlename": …, "birth": …, "year_of_study": …, "login": …, "password": …}, …] || .csv?
- `PUT("/users/edit/{id}")  # изменение основных данных пользователя`
Validators: is_admin
INPUT: {"name": …, "surname": …, "middlename": …, "birth": …, "year_of_study": …}
- `GET("/users/{id}")  # информация об основных данных пользователя`
OUTPUT: {"name": …, "surname": …, "middlename": …, "birth": …, "year_of_study": …}
- `PUT("/users/change_password/{id}")`
Validators: is_admin
INPUT: {"new_password": …}

- `GET("/users/search")  # поиск среди пользователей по ФИО и году обучения`
INPUT: {"name": …, "surname": …, "middlename": …, "birth": …, "year_of_study": …}
OUTPUT: [{…}, {…}, …]
- `DELETE("/users/delete/{id}")  # удаление пользователя из базы`
Validators: is_admin
### Работа с книгами
- `GET("/books/{id}")` | Validator: is_book_exists
- `POST("/books/create_book")` | Validator: is_librarian + is_book_exists
- `PUT("/books/edit/{id}")` | Validator: is_librarian + is_book_exists
- `DELETE("books/delete/{id}")` | Validator: is_librarian + is_book_exists

- `POST("/books/give_to_user")  # выдача книги ученику`
Validators: is_librarian + is_date_correct
INPUT: {"user_id": …, "book_id": …, "return_date": …}
- `PUT("/books/change_return_date")  # изменить срок сдачи книги`
Validators: is_librarian + is_date_correct + is_book_exists
INPUT: {"user_id": …, "book_id": …, "new_return_date": …}
- `DELETE("/books/returned") # ученик вернул книгу <=> удалить связь ученика и книги из базы`
Validators: is_librarian + is_book_exists + is_user_exists
INPUT: {"user_id": …, "book_id": …}
- `GET("/books/owns/{user_id}") # какие книги сейчас находятся у ученика`
Validators: (is_librarian || user_id == current_user.id) + is_user_exists
OUTPUT: [{"book_id": …, "return_date": ..}, {…}, …]


- `GET("/books/search/{title}")  # поиск книги по названию`
- `GET("/books/left_in_stock/{id}")  # сколько книг определённого типа осталось в наличии`
- `GET("/books/{page}")  # список всех книг. Использование пагинации`
- `POST("/books/load_csv") # загрузка книг из csv файла в базу`
Validators: is_librarian + is_data_corrupted

- `GET("/books/debtors/{page}") # получить список должников (тех, кто не вернул книгу вовремя). Использовать пагинацию`
Validators: is_librarian
