from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.open_finance_transactions import (
    get_transaction_not_synced,
    sync_transactions as sync_transactions_function,
    update_description_in_transaction_data,
    get_transactions_data,
)
from api.database.config import get_session
from typing import Annotated, List, Optional
from api.models.transaction import Transaction
from ..functions.security import get_current_user
from api.models.user import User
from api.schemas.paged_response import PagedResponseHasNext, PagedResponseFull
from api.schemas.transaction import UpdateTransactionDescription
from datetime import datetime

router = APIRouter(
    prefix="/open-finance/transactions", tags=["Open Finance Transactions"]
)


@router.get(
    "/not-synced/{account_id}", response_model=PagedResponseHasNext[Transaction]
)
async def get_not_synced_transactions(
    db: Annotated[AsyncSession, Depends(get_session)],
    account_id: str,
    user: Annotated[User, Depends(get_current_user)],
    after: str | None = Query(None, description="Cursor for pagination"),
):
    return await get_transaction_not_synced(account_id, db, after)


@router.post("/sync/{account_id}", response_model=List[Transaction])
async def sync_transactions(
    db: Annotated[AsyncSession, Depends(get_session)],
    account_id: str,
    user: Annotated[User, Depends(get_current_user)],
):
    return await sync_transactions_function(account_id, db, user)


@router.get("/", response_model=PagedResponseFull[Transaction])
async def get_transactions(
    db: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    account_id: Optional[str] = Query(
        None, description="Filtrar por uma conta específica"
    ),
    transaction_type: Optional[str] = Query(
        None, description="Filtrar por tipo (ex: credit, debit)"
    ),
    start_date: Optional[datetime] = Query(
        None, description="Data inicial do filtro (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, description="Data final do filtro (ISO format)"
    ),
    has_description: Optional[bool] = Query(
        None, description="Busca transações que tem ou não descrição"
    ),
    page: int = Query(1, ge=1, description="Número da página (mínimo 1)"),
    size: int = Query(
        20, ge=1, le=100, description="Quantidade de registros por página (máximo 100)"
    ),
):
    return await get_transactions_data(
        db=db,
        user=user,
        account_id=account_id,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        has_description=has_description,
        page=page,
        size=size,
    )


@router.patch("/description/{id}", response_model=Transaction)
async def update_description_in_transaction(
    id: str,
    data: UpdateTransactionDescription,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
):
    return await update_description_in_transaction_data(
        id=id, description=data.description, db=db, user=user
    )
