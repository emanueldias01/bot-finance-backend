from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.open_finance_transactions import get_transaction_not_synced, get_transactions, sync_transactions as sync_transactions_function
from api.database.config import get_session
from typing import Annotated, List
from api.models.transaction import Transaction
from ..functions.security import get_current_user
from api.models.user import User
from api.schemas.paged_response import PagedResponseHasNext, PagedResponseFull

router = APIRouter(
    prefix="/open-finance/transactions",
    tags=["Open Finance Transactions"]
)

@router.get("/not-synced/{account_id}", response_model=PagedResponseHasNext[Transaction])
async def get_not_synced_transactions(
    db: Annotated[AsyncSession, Depends(get_session)], 
    account_id: str, 
    user: Annotated[User, Depends(get_current_user)],
    after: str | None = Query(None, description="Cursor for pagination")
):
    return await get_transaction_not_synced(account_id, db, after)

@router.post("/sync/{account_id}", response_model=List[Transaction])
async def sync_transactions(db: Annotated[AsyncSession, Depends(get_session)], account_id: str, user: Annotated[User, Depends(get_current_user)]):
    return await sync_transactions_function(account_id, db, user)

@router.get("/synced", response_model=PagedResponseFull[Transaction])
async def get_synced_transactions(
    db: Annotated[AsyncSession, Depends(get_session)], 
    user: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page")
):
    return await get_transactions(db, user, page, page_size)
