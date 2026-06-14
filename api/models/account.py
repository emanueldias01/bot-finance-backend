from typing import Optional, List,TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from api.models.user import User


class Account(SQLModel, table=True):
    __tablename__ = "account"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="user.id", nullable=False)

    open_finance_connection: UUID
    account_id: str = Field(nullable=False)
    owner: str = Field(nullable=False)
    balance: float = Field(nullable=False)
    type: str = Field(nullable=False)
    currency_code: str = Field(nullable=False)
    transactions: List["Transaction"] = Relationship(back_populates="account")

    user: Optional["User"] = Relationship(back_populates="accounts")