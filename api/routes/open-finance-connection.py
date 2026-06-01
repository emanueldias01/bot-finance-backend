from fastapi import HTTPException
from ..functions.connect-token import obter_api_key
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("PLUGGY_BASE_URL")

@app.get("/api/pluggy/connect-token")
def create_connect_token():
    try:
        # 1. Pega a apiKey secreta do backend
        api_key = get_api_key()
        
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        
        url = f"{BASE_URL}/connect_token"
        response = requests.post(url, headers=headers)
        
        if response.status_code == 201 or response.status_code == 200:
            return {"accessToken": response.json().get("accessToken")}
        else:
            raise HTTPException(status_code=400, detail=f"Erro na Pluggy: {response.text}")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))