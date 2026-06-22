from ..models.account import Account
from ..models.transaction import Transaction
from ..models.open_finance_connection import OpenFinanceConnection
from ..models.user import User
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas.account import AccountResponse, AccountRequest, BalanceStatisticsResponse, StatisticsResponse, BalanceHistoryResponse, Month
from ..functions.open_finance_item import get_api_key
import requests
from ..schemas.pluggy_account_response import PluggyAccountResponse
from typing import List
from datetime import datetime, timedelta

from dotenv import load_dotenv
import os

load_dotenv()

BASE_URL = os.getenv("AGGREGATE_BASE_URL")
API_KEY = os.getenv("AGGREGATE_API_KEY")

URL = f"{BASE_URL}/accounts"

HEADERS = {"X-API-KEY": None, "Content-Type": "application/json"}

MONTHS = {
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dec"
}


async def _return_response(
    results: List[PluggyAccountResponse], db: AsyncSession
) -> List[AccountResponse]:
    response: List[AccountResponse] = []
    for result in results:
        exists = await db.execute(
            select(Account).where(Account.account_id == result.get("id"))
        )
        if exists.scalar_one_or_none():
            continue

        response.append(
            _map_to_response(
                {
                    "id": None,
                    "open_finance_connection": None,
                    "account_id": result.get("id"),
                    "owner": result.get("owner"),
                    "balance": result.get("balance"),
                    "type": result.get("type"),
                    "currency_code": result.get("currencyCode"),
                }
            )
        )
    return response


def _map_to_response(account: dict) -> AccountResponse:
    return AccountResponse(
        id=account.get("id"),
        open_finance_connection=account.get("open_finance_connection"),
        account_id=account.get("account_id"),
        owner=account.get("owner"),
        balance=account.get("balance"),
        type=account.get("type"),
        currency_code=account.get("currency_code"),
    )


async def get_accounts_not_connected(itemId: str, type: str | None, db: AsyncSession):
    op_connection: OpenFinanceConnection | None = await db.get(
        OpenFinanceConnection, itemId
    )
    if not op_connection:
        raise HTTPException(status_code=404, detail="Open Finance Connection not found")

    if API_KEY:
        HEADERS["X-API-KEY"] = API_KEY
    else:
        api_key = await get_api_key()
        os.environ["AGGREGATE_API_KEY"] = api_key
        HEADERS["X-API-KEY"] = api_key

    url = f"{URL}?itemId={op_connection.pluggy_connection_id}"
    if type:
        url += f"&type={type}"
    res = requests.get(url, headers=HEADERS)

    if res.status_code == 200:
        results = res.json()["results"]
        return await _return_response(results, db)
    elif res.status_code == 403:
        api_key = await get_api_key()
        HEADERS["X-API-KEY"] = api_key
        os.environ["AGGREGATE_API_KEY"] = api_key
        res = requests.get(url, headers=HEADERS)

        if res.status_code == 200:
            results = res.json()["results"]
            return await _return_response(results, db)
        else:
            raise HTTPException(status_code=res.status_code, detail=res.text)
    else:
        raise HTTPException(status_code=res.status_code, detail=res.text)


async def get_accounts_connected(db: AsyncSession, user: User) -> List[AccountResponse]:
    accounts = await db.execute(select(Account).where(Account.user_id == user.id))

    response = []
    for account in accounts.scalars().all():
        response.append(AccountResponse(**account.__dict__))

    return response


async def create_account(
    request: AccountRequest, db: AsyncSession, user: User
) -> AccountResponse:
    connection = await db.execute(
        select(OpenFinanceConnection).where(
            OpenFinanceConnection.id == request.open_finance_connection
        )
    )
    connection = connection.scalar_one_or_none()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    account = Account(**request.model_dump(), user_id=user.id)
    db.add(account)
    await db.commit()
    await db.refresh(account)

    return AccountResponse(**account.model_dump())

async def get_balance_statistics(db: AsyncSession, user: User):
    total = await db.execute(select(func.sum(Account.balance)).where(Account.user_id == user.id))

    firstDay = datetime.now().replace(day=1)
    lastDay = datetime.now().replace(day=1) + timedelta(days=30)

    revenues = await db.execute(select(func.sum(Transaction.amount)).where(Transaction.user_id == user.id).where(
        Transaction.type == "CREDIT" and Transaction.date >= firstDay and Transaction.date < lastDay
    ))
    expenses = await db.execute(select(func.sum(Transaction.amount)).where(Transaction.user_id == user.id).where(
        Transaction.type == "DEBIT" and Transaction.date >= firstDay and Transaction.date < lastDay
    ))

    response = BalanceStatisticsResponse(
        total=total.scalar_one_or_none() or 0,
        statistics=StatisticsResponse(
            month=MONTHS[datetime.now().month],
            revenues=revenues.scalar_one_or_none() or 0,
            expenses=expenses.scalar_one_or_none() or 0
        )
    )

    return response


async def get_balance_history(db: AsyncSession, user: User):
    today = datetime.now()
    
    chronological_months = []
    target_month = today.month
    target_year = today.year
    
    for _ in range(6):
        chronological_months.insert(0, (target_year, target_month))
        target_month -= 1
        if target_month == 0:
            target_month = 12
            target_year -= 1

    start_date = datetime(chronological_months[0][0], chronological_months[0][1], 1)
    end_date = today

    revenue_query = """
    SELECT 
        EXTRACT(YEAR FROM date) as year,
        EXTRACT(MONTH FROM date) as month,
        SUM(amount) as total
    FROM transaction 
    WHERE user_id = :user_id 
        AND type = 'CREDIT'
        AND date >= :start_date
        AND date <= :end_date
    GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
    ORDER BY year, month
    """
    
    expense_query = """
    SELECT 
        EXTRACT(YEAR FROM date) as year,
        EXTRACT(MONTH FROM date) as month,
        SUM(amount) as total
    FROM transaction 
    WHERE user_id = :user_id 
        AND type = 'DEBIT'
        AND date >= :start_date
        AND date <= :end_date
    GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
    ORDER BY year, month
    """

    revenue_result = await db.execute(
        text(revenue_query),
        {"user_id": user.id, "start_date": start_date, "end_date": end_date}
    )
    
    expense_result = await db.execute(
        text(expense_query),
        {"user_id": user.id, "start_date": start_date, "end_date": end_date}
    )

    revenue_map = {(int(row.year), int(row.month)): float(row.total) for row in revenue_result.fetchall()}
    expense_map = {(int(row.year), int(row.month)): float(row.total) for row in expense_result.fetchall()}

    revenue_months = []
    expense_months = []
    total_revenue = 0.0
    total_expense = 0.0

    for year, month in chronological_months:
        rev_value = revenue_map.get((year, month), 0.0)
        exp_value = expense_map.get((year, month), 0.0)
        
        total_revenue += rev_value
        total_expense += exp_value

        revenue_months.append(Month(month=MONTHS[month], value=rev_value))
        expense_months.append(Month(month=MONTHS[month], value=exp_value))
    
    response = BalanceHistoryResponse(
        revenue_months=revenue_months,
        expense_months=expense_months,
        total=total_revenue - total_expense
    )
    
    return response
