from fastapi import APIRouter
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Query
from fastapi import HTTPException

from api.schemas.account import AccountRequest, AccountResponse, PluggyAccountTypeEnum
from ..functions.open_finance_account import (
    get_accounts_not_connected,
    get_accounts_connected,
    create_account,
)
from ..database.config import get_session
from ..functions.security import get_current_user
from api.models.user import User

router = APIRouter(prefix="/open-finance/accounts", tags=["Open Finance Accounts"])


@router.get("/not-synced/")
async def get_not_connected_accounts(
    db: Annotated[AsyncSession, Depends(get_session)],
    itemId: str,
    user: User = Depends(get_current_user),
    type: PluggyAccountTypeEnum | None = Query(None, alias="type"),
):
    return await get_accounts_not_connected(itemId, type.value if type else None, db)


@router.get("/synced/")
async def get_connected_accounts(db: Annotated[AsyncSession, Depends(get_session)], user: User = Depends(get_current_user)):
    return await get_accounts_connected(db, user)


@router.post("/")
async def create(
    data: AccountRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
) -> AccountResponse:
    return await create_account(data, db, user)
