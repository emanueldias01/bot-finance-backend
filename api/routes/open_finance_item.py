from fastapi import HTTPException, APIRouter
from ..functions.open_finance_item import (
    connect_token,
    create_item,
    list_items,
    get_item,
)
import requests
import os
from dotenv import load_dotenv
from ..schemas.open_finance import OpenFinanceItemRequest, OpenFinanceItemResponse
from api.database.config import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated
from fastapi import Depends
from ..functions.security import get_current_user
from api.models.user import User

load_dotenv()

BASE_URL = os.getenv("PLUGGY_BASE_URL")

router = APIRouter(prefix="/open-finance", tags=["Open Finance"])


@router.post("/connect-token")
async def create_connect_token(user: User = Depends(get_current_user)):
    try:
        return await connect_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/item", response_model=OpenFinanceItemResponse)
async def create(
    request: OpenFinanceItemRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    try:
        return await create_item(request, db, user)
    except Exception as e:
        raise HTTPException(status_code=500)


@router.get("/items", response_model=list[OpenFinanceItemResponse])
async def list(
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    try:
        return await list_items(db, user)
    except Exception as e:
        raise HTTPException(status_code=500)


@router.get("/item/{id}", response_model=OpenFinanceItemResponse)
async def get(
    id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    try:
        return await get_item(id, db)
    except Exception as e:
        raise HTTPException(status_code=500)
