import os
from re import A
import requests
from dotenv import load_dotenv
from ..schemas.open_finance import OpenFinanceItemRequest, OpenFinanceItemResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, delete
from ..models.open_finance_connection import OpenFinanceConnection
from ..models.transaction import Transaction
from ..models.account import Account
from ..models.user import User
from fastapi import HTTPException
from uuid import UUID

load_dotenv()

CLIENT_ID = os.getenv("AGGREGATE_CLIENT_ID")
CLIENT_SECRET = os.getenv("AGGREGATE_CLIENT_SECRET")
BASE_URL = os.getenv("AGGREGATE_BASE_URL")
API_KEY = os.getenv("AGGREGATE_API_KEY")


async def get_api_key():
    url = f"{BASE_URL}/auth"
    payload = {
        "clientSecret": CLIENT_SECRET,
        "clientId": CLIENT_ID,
    }

    headers = {"Content-Type": "application/json", "Accept": "application/json"}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json().get("apiKey")
    else:
        raise Exception(f"Error: {response.text}")


async def connect_token():
    api_key = API_KEY or await get_api_key()

    headers = {"X-API-KEY": api_key, "Content-Type": "application/json"}

    url = f"{BASE_URL}/connect_token"
    response = requests.post(url, headers=headers)

    if response.status_code == 201 or response.status_code == 200:
        return response.json()
    elif response.status_code == 403:
        api_key = await get_api_key()

        headers["X-API-KEY"] = api_key
        os.environ["AGGREGATE_API_KEY"] = api_key

        response = requests.post(url, headers=headers)

        return response.json()
    else:
        raise Exception(f"Error: {response.text}")


async def create_item(request: OpenFinanceItemRequest, db: AsyncSession, user: User):
    connectionAlreadyExists = await db.execute(
        select(OpenFinanceConnection).where(
            OpenFinanceConnection.pluggy_connection_id == request.pluggy_connection_id
        )
    )

    if connectionAlreadyExists.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Connection already exists")

    open_finance_connection = OpenFinanceConnection(
        user_id=user.id,
        pluggy_connection_id=request.pluggy_connection_id,
        institution_image_url=request.institution_image_url,
        institution_name=request.institution_name,
        status=request.status,
        consent_expires_at=request.consent_expires_at,
    )

    db.add(open_finance_connection)
    await db.commit()
    await db.refresh(open_finance_connection)

    return open_finance_connection


async def list_items(db: AsyncSession, user: User):
    result = await db.execute(
        select(OpenFinanceConnection).where(OpenFinanceConnection.user_id == user.id)
    )
    return [OpenFinanceItemResponse(**item.__dict__) for item in result.scalars().all()]


async def get_item(id: str, db: AsyncSession):
    result = await db.execute(
        select(OpenFinanceConnection).where(OpenFinanceConnection.id == id)
    )

    if not result.scalar_one():
        raise HTTPException(status_code=404, detail="Open finance connection not found")

    return OpenFinanceItemResponse(**result.scalar_one().__dict__)

async def unsync_item(item_id: str, db: AsyncSession):
    try:
        connection_result = await db.execute(
            select(OpenFinanceConnection).where(OpenFinanceConnection.id == UUID(item_id))
        )
        connection = connection_result.scalar_one_or_none()

        if not connection:
            raise HTTPException(status_code=404, detail="Open finance connection not found")

        accounts_result = await db.execute(
            select(Account).where(Account.open_finance_connection == connection.id)
        )
        accounts = accounts_result.scalars().all()

        if accounts:
            account_ids = [account.id for account in accounts]
            await db.execute(
                delete(Transaction).where(Transaction.account_id.in_(account_ids))
            )

        await db.execute(
            delete(Account).where(Account.open_finance_connection == connection.id)
        )

        await db.execute(
            delete(OpenFinanceConnection).where(OpenFinanceConnection.id == connection.id)
        )

        await db.commit()
        return {"message": "Item unsynced successfully"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))