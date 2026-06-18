from fastapi import APIRouter, Depends
from api.schemas.user import UserRequest, UserResponse
from api.schemas.token import TokenResponse
from api.functions.auth import register, login
from sqlalchemy.ext.asyncio import AsyncSession
from api.database.config import get_session
from typing import Annotated


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(
    data: UserRequest, db: Annotated[AsyncSession, Depends(get_session)]
) -> UserResponse:
    return await register(data=data, db=db)


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login_user(
    data: UserRequest, db: Annotated[AsyncSession, Depends(get_session)]
) -> TokenResponse:
    return await login(data=data, db=db)
