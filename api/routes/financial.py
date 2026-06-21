from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.models.financial import Payable, Receivable
from api.models.user import User
from api.schemas.financial import PayableRequest, PayableResponse, ReceivableRequest, ReceivableResponse
from api.database.config import get_session
from api.functions.security import get_current_user

router = APIRouter(prefix="/financial", tags=["Financial"])


@router.get("/payables", response_model=List[PayableResponse])
async def get_payables(
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payable).where(Payable.user_id == user.id)
    )
    return result.scalars().all()


@router.post("/payables", response_model=PayableResponse)
async def create_payable(
    data: PayableRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    payable = Payable(**data.dict(), user_id=user.id)
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    return payable


@router.put("/payables/{payable_id}", response_model=PayableResponse)
async def update_payable(
    payable_id: str,
    data: PayableRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payable).where(Payable.id == payable_id, Payable.user_id == user.id)
    )
    payable = result.scalar_one_or_none()
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")
    
    for key, value in data.dict().items():
        setattr(payable, key, value)
    
    db.add(payable)
    await db.commit()
    await db.refresh(payable)
    return payable


@router.delete("/payables/{payable_id}")
async def delete_payable(
    payable_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Payable).where(Payable.id == payable_id, Payable.user_id == user.id)
    )
    payable = result.scalar_one_or_none()
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")
    
    await db.delete(payable)
    await db.commit()
    return {"message": "Payable deleted"}


@router.get("/receivables", response_model=List[ReceivableResponse])
async def get_receivables(
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Receivable).where(Receivable.user_id == user.id)
    )
    return result.scalars().all()


@router.post("/receivables", response_model=ReceivableResponse)
async def create_receivable(
    data: ReceivableRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    receivable = Receivable(**data.dict(), user_id=user.id)
    db.add(receivable)
    await db.commit()
    await db.refresh(receivable)
    return receivable


@router.put("/receivables/{receivable_id}", response_model=ReceivableResponse)
async def update_receivable(
    receivable_id: str,
    data: ReceivableRequest,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Receivable).where(Receivable.id == receivable_id, Receivable.user_id == user.id)
    )
    receivable = result.scalar_one_or_none()
    if not receivable:
        raise HTTPException(status_code=404, detail="Receivable not found")
    
    for key, value in data.dict().items():
        setattr(receivable, key, value)
    
    db.add(receivable)
    await db.commit()
    await db.refresh(receivable)
    return receivable


@router.delete("/receivables/{receivable_id}")
async def delete_receivable(
    receivable_id: str,
    db: Annotated[AsyncSession, Depends(get_session)],
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Receivable).where(Receivable.id == receivable_id, Receivable.user_id == user.id)
    )
    receivable = result.scalar_one_or_none()
    if not receivable:
        raise HTTPException(status_code=404, detail="Receivable not found")
    
    await db.delete(receivable)
    await db.commit()
    return {"message": "Receivable deleted"}
