from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class Transaction(SQLModel, table=True):
    __tablename__ = "transaction"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    account_id: UUID = Field(foreign_key="account.id")
    transaction_id: str = Field(unique=True, index=True, nullable=False)
    amount: float = Field(nullable=False)
    description: str = Field(nullable=False)
    date: date = Field(nullable=False)
    type: str = Field(nullable=False)
    currency_code: str = Field(nullable=False)