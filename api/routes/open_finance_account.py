from fastapi import APIRouter
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Query
from fastapi import HTTPException

from api.schemas.account import AccountRequest, AccountResponse, PluggyAccountTypeEnum
from ..functions.open_finance_account import get_accounts_not_connected, get_accounts_connected, create_account
from ..database.config import get_session

router = APIRouter(
    prefix="/api/open-finance/accounts",
    tags=["Open Finance Accounts"]
)

@router.get("/not-connected/{itemId}")
async def get_not_connected_accounts(db: Annotated[AsyncSession, Depends(get_session)], itemId: str, type: PluggyAccountTypeEnum | None = Query(None, alias="type")):
    return await get_accounts_not_connected(itemId, type.value if type else None, db)

@router.get("/connected/{itemId}")
async def get_connected_accounts(db: Annotated[AsyncSession, Depends(get_session)], itemId: str):
    return await get_accounts_connected(db, itemId)

@router.post("/")
async def create(data: AccountRequest, db: Annotated[AsyncSession, Depends(get_session)]) -> AccountResponse:
    return await create_account(data, db)

