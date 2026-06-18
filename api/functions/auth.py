from api.schemas.user import UserRequest, UserResponse, UserLogin
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from api.functions.security import verify_password, hash_password, create_access_token
from api.models.user import User
from api.schemas.token import TokenResponse
from fastapi import HTTPException


async def register(data: UserRequest, db: AsyncSession) -> UserResponse:
    result = await db.execute(select(User).where(User.username == data.username))
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(status_code=409, detail="This user already exists")

    password_encrypt = hash_password(data.password)

    user = User(**data.model_dump(exclude={"password"}), password=password_encrypt)

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def login(data: UserLogin, db: AsyncSession) -> TokenResponse:
    user = (
        await db.execute(select(User).where(User.username == data.username))
    ).scalar_one_or_none()

    if not user or not verify_password(data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    token = create_access_token(user)

    return TokenResponse(token=token)
