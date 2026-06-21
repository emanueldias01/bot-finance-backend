from typing import Optional, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from api.models.user import User


class Payable(SQLModel, table=True):
    __tablename__ = "payable"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    
    description: str = Field(nullable=False)
    category: str = Field(nullable=False)
    value: float = Field(nullable=False)
    due_date: datetime = Field(nullable=False)
    status: str = Field(default="pending", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional["User"] = Relationship(back_populates="payables")


class Receivable(SQLModel, table=True):
    __tablename__ = "receivable"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)
    
    client: str = Field(nullable=False)
    value: float = Field(nullable=False)
    forecast_date: datetime = Field(nullable=False)
    status: str = Field(default="pending", nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    user: Optional["User"] = Relationship(back_populates="receivables")
