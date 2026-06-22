from fastapi import APIRouter, Depends
from api.functions.llm_chat import request_chat_about_account, analyze_transactions_insights
from api.schemas.chat import ChatRequestTransactions, ChatResponse, InsightsResponse
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


@router.get("/insights", response_model=InsightsResponse)
async def get_insights(
    db: AsyncSession = Depends(get_session),
    user: User = Depends(get_current_user),
):
    try:
        return await analyze_transactions_insights(db=db, user=user)
    except Exception as e:
        print(f"Error parsing insights: {e}")
        return InsightsResponse(
            insights=[],
            has_transactions=False,
            summary="Não foi possível gerar insights neste momento. Haverá uma nova tentativa em breve."
        )