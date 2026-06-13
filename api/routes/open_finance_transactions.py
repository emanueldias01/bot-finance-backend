from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.open_finance_transactions import get_transaction_not_synced, get_transactions, sync_transactions as sync_transactions_function
from api.database.config import get_session
from typing import Annotated, List
from api.models.transaction import Transaction

router = APIRouter(
    prefix="/api/open-finance/transactions",
    tags=["Open Finance Transactions"]
)

@router.get("/not-synced/{account_id}", response_model=List[Transaction])
async def get_not_synced_transactions(db: Annotated[AsyncSession, Depends(get_session)], account_id: str):
    return await get_transaction_not_synced(account_id, db)

@router.post("/sync/{account_id}", response_model=List[Transaction])
async def sync_transactions(db: Annotated[AsyncSession, Depends(get_session)], account_id: str):
    return await sync_transactions_function(account_id, db)

@router.get("/synced/{account_id}", response_model=List[Transaction])
async def get_synced_transactions(db: Annotated[AsyncSession, Depends(get_session)], account_id: str):
    return await get_transactions(db, account_id)
