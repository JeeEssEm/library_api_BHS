from auth.views import router as auth_router
import fastapi

app = fastapi.FastAPI()
app.include_router(auth_router, prefix='/users')
