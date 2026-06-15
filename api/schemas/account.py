from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date
from typing import Optional, List, Any
from enum import Enum

class PluggyAccountTypeEnum(Enum):
    BANK = "BANK"
    CREDIT = "CREDIT"

class AccountResponse(BaseModel):
    id: UUID | None = None
    open_finance_connection: UUID | None = None
    account_id: str
    owner: str | None = None
    balance: float
    type: str
    currency_code: str
    user_id: UUID | None = None

class AccountRequest(BaseModel):
    open_finance_connection: UUID
    account_id: str
    owner: str
    balance: float
    type: str
    currency_code: str