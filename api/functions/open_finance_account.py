from ..models.account import Account
from ..models.open_finance_connection import OpenFinanceConnection
from ..models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from ..schemas.account import AccountResponse
from ..functions.open_finance_item import get_api_key
import requests
from ..schemas.pluggy_account_response import PluggyAccountResponse

from dotenv import load_dotenv
import os

load_dotenv()

CLIENT_ID = os.getenv("AGGREGATE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AGGREGATE_CLIENT_SECRET")
BASE_URL = os.getenv("AGGREGATE_BASE_URL")
API_KEY = os.getenv("AGGREGATE_API_KEY")

URL = f"{BASE_URL}/accounts"

HEADERS = {
    "X-API-KEY": None,
    "Content-Type": "application/json"
}


def mapToResponse(account: dict) -> AccountResponse:
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
    op_connection: OpenFinanceConnection | None = await db.get(OpenFinanceConnection, itemId)
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
        response: List[AccountResponse]= []
        for result in res.json()["results"]:
            response.append(mapToResponse({
                "id": None,
                "open_finance_connection": None,
                "account_id": result.get("id"),
                "owner": result.get("owner"),
                "balance": result.get("balance"),
                "type": result.get("name"),
                "currency_code": result.get("currencyCode"),
            }))
            
        return response
    elif res.status_code == 403:
        HEADERS["X-API-KEY"] = await get_api_key()
        res = requests.get(url, headers=HEADERS)
        response: List[AccountResponse]= []
        for result in res.json()["results"]:
            response.append(mapToResponse({
                "id": None,
                "open_finance_connection": None,
                "account_id": result.get("id"),
                "owner": result.get("owner"),
                "balance": result.get("balance"),
                "type": result.get("name"),
                "currency_code": result.get("currencyCode"),
            }))
            
        if res.status_code == 200:
            return response
        else:
            raise HTTPException(status_code=res.status_code, detail=res.text)
    else:
        raise HTTPException(status_code=res.status_code, detail=res.text)
   
async def get_accounts_connected(db: AsyncSession) -> List[AccountResponse]:
    accounts = await db.execute(select(Account))
    return accounts.scalars().all()

async def create_account(request: str, db: AsyncSession) -> AccountResponse:
    connection = db.execute(select(OpenFinanceConnection).where(OpenFinanceConnection.id == request))
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    account = Account(**request.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    
    return AccountResponse(**account.model_dump())
    
    