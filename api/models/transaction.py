from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    account_id: UUID = Field(foreign_key="account.id")
    transaction_id: str = Field(unique=True, index=True, nullable=False)
    amount: float = Field(nullable=False)
    description: str = Field(nullable=False)
    date: datetime = Field(nullable=False)
    type: str = Field(nullable=False)
    currency_code: str = Field(nullable=False)
    user_id: UUID = Field(foreign_key="user.id")

    # Relationships
    account: Optional["Account"] = Relationship(back_populates="transactions")
    user: Optional["User"] = Relationship(back_populates="transactions")