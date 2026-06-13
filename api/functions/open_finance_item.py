import os
import requests
from dotenv import load_dotenv
from ..schemas.open_finance import OpenFinanceItemRequest, OpenFinanceItemResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from ..models.open_finance_connection import OpenFinanceConnection
from fastapi import HTTPException

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

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("apiKey")
    else:
        raise Exception(f"Error: {response.text}")

async def connect_token():
    api_key = API_KEY or await get_api_key() 
    
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json"
    }
    
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

async def create_item(request: OpenFinanceItemRequest, db: AsyncSession):
    open_finance_connection = OpenFinanceConnection(
        user_id=request.user_id,
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

async def list_items(db: AsyncSession):
    result = await db.execute(select(OpenFinanceConnection))
    return [OpenFinanceItemResponse(**item.__dict__) for item in result.scalars().all()]

async def get_item(id: str, db: AsyncSession):
    result = await db.execute(select(OpenFinanceConnection).where(OpenFinanceConnection.id == id))

    if not result.scalar_one():
        raise HTTPException(status_code=404, detail="Open finance connection not found")
    
    return OpenFinanceItemResponse(**result.scalar_one().__dict__)



    