from fastapi import FastAPI
from api.routes.auth import router as auth_router

app = FastAPI(
    version="0.0.1"
)

app.include_router(auth_router)