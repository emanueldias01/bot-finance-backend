import os
import requests
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("PLUGGY_CLIENT_ID")
CLIENT_SECRET = os.getenv("PLUGGY_CLIENT_SECRET")
BASE_URL = os.getenv("PLUGGY_BASE_URL")

def get_api_key():
    url = f"{BASE_URL}/auth"
    payload = {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        return response.json().get("apiKey")
    else:
        raise Exception(f"Error: {response.text}")