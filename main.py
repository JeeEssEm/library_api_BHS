from auth.views import router as auth_router
from users.views import router as users_router
from books.views import router as books_router
import fastapi

app = fastapi.FastAPI()
app.include_router(auth_router, prefix='/auth', tags=['auth'])
app.include_router(users_router, prefix='/users', tags=['users'])
app.include_router(books_router, prefix='/books', tags=['books'])
