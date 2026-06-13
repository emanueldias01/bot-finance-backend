from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class Account(SQLModel, table=True):
    __tablename__ = "account"
    
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    open_finance_connection: UUID
    account_id: str = Field(nullable=False)
    owner: str = Field(nullable=False)
    balance: float = Field(nullable=False)
    type: str = Field(nullable=False)
    currency_code: str = Field(nullable=False)
