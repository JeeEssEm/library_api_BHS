from auth.views import router as auth_router
from users.views import router as users_router
import fastapi

app = fastapi.FastAPI()
app.include_router(auth_router, prefix='/auth')
app.include_router(users_router, prefix='/users')
