from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from api.models.transaction import Transaction
from api.models.account import Account
from api.models.user import User
from api.schemas.pluggy_transaction_response import PluggyTransactionResponse
from api.schemas.paged_response import PagedResponseHasNext, PagedResponseFull
from .open_finance_item import get_api_key
import requests
from fastapi import HTTPException
from datetime import datetime

from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("AGGREGATE_BASE_URL")
API_KEY = os.getenv("AGGREGATE_API_KEY")

URL = f"{BASE_URL}/v2/transactions"

HEADERS = {"X-API-KEY": None, "Content-Type": "application/json"}


async def _return_response(
    transaction: List[PluggyTransactionResponse], db: AsyncSession, account_id: str
) -> List[Transaction]:
    transactions = []
    for t in transaction:
        exists = await db.execute(
            select(Transaction).where(Transaction.transaction_id == t.get("id"))
        )
        if exists.scalar_one_or_none():
            continue

        transactions.append(
            Transaction(
                account_id=account_id,
                transaction_id=t.get("id"),
                amount=t.get("amount"),
                description=t.get("description"),
                date=datetime.fromisoformat(t.get("date").replace("Z", "")),
                type=t.get("type"),
                currency_code=t.get("currencyCode"),
            )
        )

    return transactions


async def get_transaction_not_synced(
    accountId: str, db: AsyncSession, after: str | None = None
) -> PagedResponseHasNext[Transaction]:
    account: Account | None = await db.execute(
        select(Account).where(Account.id == accountId)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if API_KEY:
        HEADERS["X-API-KEY"] = API_KEY
    else:
        api_key = await get_api_key()
        os.environ["AGGREGATE_API_KEY"] = api_key
        HEADERS["X-API-KEY"] = api_key

    account_data = account.scalar_one()
    url = f"{URL}?accountId={account_data.account_id}"
    if after:
        url += f"&after={after}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        data = response.json()
        after_str = data.get("next").split("after=")[1] if data.get("next") else None
        transactions = await _return_response(data["results"], db, accountId)
        return PagedResponseHasNext(
            has_next=data.get("next") is not None, after=after_str, results=transactions
        )
    elif response.status_code == 403:
        api_key = await get_api_key()
        HEADERS["X-API-KEY"] = api_key
        os.environ["AGGREGATE_API_KEY"] = api_key
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            transactions = await _return_response(data["results"], db, accountId)
            after_str = (
                data.get("next").split("after=")[1] if data.get("next") else None
            )
            return PagedResponseHasNext(
                has_next=data.get("next") is not None,
                after=after_str,
                results=transactions,
            )
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    else:
        raise HTTPException(status_code=500, detail="Unknown error")


async def _get_all_transaction_not_synced(
    accountId: str, db: AsyncSession
) -> List[Transaction]:
    account: Account | None = await db.execute(
        select(Account).where(Account.id == accountId)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if API_KEY:
        HEADERS["X-API-KEY"] = API_KEY
    else:
        api_key = await get_api_key()
        os.environ["AGGREGATE_API_KEY"] = api_key
        HEADERS["X-API-KEY"] = api_key

    account_data = account.scalar_one()
    all_transactions = []
    next_cursor = None

    while True:
        url = f"{URL}?accountId={account_data.account_id}"
        if next_cursor:
            url += f"&after={next_cursor}"

        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            all_transactions.extend(data["results"])
            next_cursor = data.get("next")

            if not next_cursor:
                break
        elif response.status_code == 403:
            api_key = await get_api_key()
            HEADERS["X-API-KEY"] = api_key
            os.environ["AGGREGATE_API_KEY"] = api_key
            response = requests.get(url, headers=HEADERS)
            if response.status_code == 200:
                data = response.json()
                all_transactions.extend(data["results"])
                next_cursor = data.get("next")

                if not next_cursor:
                    break
            else:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )
        else:
            raise HTTPException(status_code=500, detail="Unknown error")

    return await _return_response(all_transactions, db, accountId)


async def sync_transactions(
    user_id: str, db: AsyncSession, user: User
) -> List[Transaction]:

    transactions: List[Transaction] = await _get_all_transaction_not_synced(user_id, db)

    for transaction in transactions:
        transaction.user_id = user.id
        db.add(transaction)

    await db.commit()
    return transactions


async def update_description_in_transaction_data(
    id: str, description: str, db: AsyncSession, user: User
) -> Transaction:
    transaction = await db.get(Transaction, id)

    if transaction is None:
        HTTPException(404, "Transaction not found")

    account = await db.get(Account, transaction.account_id)

    if account is None:
        HTTPException(404, "Account not found")

    if account.user_id != user.id:
        HTTPException(409, "Unauthorized access")

    transaction.description = description

    db.add(transaction)
    await db.commit()

    return transaction


async def get_transactions_data(
    db: AsyncSession,
    user: User,
    account_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    has_description: Optional[bool] = False,
    page: int = 1,
    size: int = 20,
) -> PagedResponseFull[Transaction]:
    if page < 1:
        page = 1
    if size < 1 or size > 100:
        size = 20

    offset = (page - 1) * size

    query = select(Transaction).where(Transaction.user_id == user.id)

    if account_id:
        query = query.where(Transaction.account_id == account_id)

    if transaction_type:
        query = query.where(Transaction.type == transaction_type.lower())

    if start_date:
        query = query.where(Transaction.date >= start_date)

    if end_date:
        query = query.where(Transaction.date <= end_date)

    if has_description:
        query = query.where(Transaction.description != "")
    else:
        query = query.where(Transaction.description == "")

    count_query = select(func.count()).select_from(Transaction).where(Transaction.user_id == user.id)
    
    if account_id:
        count_query = count_query.where(Transaction.account_id == account_id)

    if transaction_type:
        count_query = count_query.where(Transaction.type == transaction_type.lower())

    if start_date:
        count_query = count_query.where(Transaction.date >= start_date)

    if end_date:
        count_query = count_query.where(Transaction.date <= end_date)

    if has_description:
        count_query = count_query.where(Transaction.description != "")
    else:
        count_query = count_query.where(Transaction.description == "")

    try:
        count_result = await db.execute(count_query)
        total = count_result.scalar()
        total_pages = (total + size - 1) // size if total > 0 else 1

        query = query.order_by(Transaction.date.desc()).offset(offset).limit(size)
        result = await db.execute(query)
        transactions = result.scalars().all()
        
        return PagedResponseFull(
            page=page,
            total_pages=total_pages,
            total=total,
            results=list(transactions)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Erro interno ao buscar transações."
        )


async def get_transactions_by_period(
    db: AsyncSession,
    user_id: str,
    start_date: datetime,
    end_date: datetime,
) -> list[Transaction]:
    statement = (
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .where(Transaction.description != "")
        .where(Transaction.date >= start_date)
        .where(Transaction.date <= end_date)
        .order_by(Transaction.date.desc())
    )

    result = await db.execute(statement)
    return result.scalars().all()
