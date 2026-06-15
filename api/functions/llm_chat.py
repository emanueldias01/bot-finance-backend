from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.open_finance_transactions import get_transactions
from api.schemas.chat import ChatRequestTransactions, ChatResponse
from api.models.user import User
from api.models.account import Account
from sqlalchemy import select
from fastapi import HTTPException
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

AI_API_KEY = os.getenv("AI_API_KEY")

async def request_chat_about_account(request: ChatRequestTransactions, db: AsyncSession, user: User) -> ChatResponse:
    verify_accout = await db.execute(
        select(User).where(User.id == user.id).join(User.accounts).where(Account.id == request.account_id)
    )
    if not verify_accout.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")

    result = await get_transactions(db=db, account_id=request.account_id)
    client = genai.Client(api_key=AI_API_KEY)

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=f"""Com base nas transações do usuário, responda sua pergunta:

        transações: {result}

        pergunta: {request.message}
        
        
        """
    )

    return ChatResponse(response=response.text)

