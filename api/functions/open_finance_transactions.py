from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from api.models.transaction import Transaction
from api.models.account import Account
from api.schemas.pluggy_transaction_response import PluggyTransactionResponse
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

HEADERS = {
    "X-API-KEY": None,
    "Content-Type": "application/json"
}


async def _return_response(transaction: List[PluggyTransactionResponse], db: AsyncSession, account_id: str) -> List[Transaction]:
    transactions = []
    for t in transaction:
        exists = await db.execute(select(Transaction).where(Transaction.transaction_id == t.get("id")))
        if exists.scalar_one_or_none():
            continue

        transactions.append(Transaction(
            account_id=account_id,
            transaction_id=t.get("id"),
            amount=t.get("amount"),
            description=t.get("description"),
            date=datetime.fromisoformat(t.get("date").replace("Z", "")),
            type=t.get("type"),
            currency_code=t.get("currencyCode"),
        ))

    return transactions
    

async def get_transactions(db: AsyncSession, account_id: str) -> List[Transaction]:
    transactions = await db.execute(select(Transaction).where(Transaction.account_id == account_id))
    return transactions.scalars().all()

async def get_transaction_not_synced(accountId: str, db: AsyncSession) -> List[Transaction]:
    account: Account | None = await db.execute(select(Account).where(Account.id == accountId))
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if API_KEY:
        HEADERS["X-API-KEY"] = API_KEY
    else:
        api_key = await get_api_key()
        os.environ["AGGREGATE_API_KEY"] = api_key
        HEADERS["X-API-KEY"] = api_key

    url = f"{URL}?accountId={account.scalar_one().account_id}"

    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return await _return_response(response.json()['results'], db, accountId)
    elif response.status_code == 403:
        api_key = await get_api_key()
        HEADERS["X-API-KEY"] = api_key
        os.environ["AGGREGATE_API_KEY"] = api_key
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            return await _return_response(response.json()['results'], db, accountId)
        else:
            raise HTTPException(status_code=response.status_code, detail=response.text)
    else:
        raise HTTPException(status_code=500, detail="Unknown error")


async def sync_transactions(accountId: str, db: AsyncSession) -> List[Transaction]:
    transactions: List[Transaction] = await get_transaction_not_synced(accountId, db)

    for transaction in transactions:
        db.add(transaction)
    await db.commit()
    return transactions


