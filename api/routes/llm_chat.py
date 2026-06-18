from fastapi import APIRouter, Depends
from api.functions.llm_chat import request_chat_about_account
from api.schemas.chat import ChatRequestTransactions, ChatResponse
from sqlalchemy.ext.asyncio import AsyncSession
from api.functions.security import get_current_user
from api.models.user import User
from api.database.config import get_session

router = APIRouter(prefix="/llm-chat", tags=["llm-chat"])


@router.post("/transactions", response_model=ChatResponse)
async def chat_about_account(
    request: ChatRequestTransactions,
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    return await request_chat_about_account(request=request, db=db, user=user)
