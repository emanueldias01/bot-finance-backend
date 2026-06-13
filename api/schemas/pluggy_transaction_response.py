from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Any

class PluggyTransactionResponse(BaseModel):
    id: str
    description: str
    descriptionRaw: Optional[str] = None
    currencyCode: str
    amount: float
    amountInAccountCurrency: Optional[float] = None
    date: datetime
    category: Optional[str] = None
    categoryId: Optional[str] = None
    balance: Optional[float] = None
    accountId: str
    providerCode: Optional[str] = None
    status: str
    paymentData: Optional[Any] = None
    type: str
    operationType: Optional[str] = None
    operationTypeAdditionalInfo: Optional[str] = None
    creditCardMetadata: Optional[Any] = None
    acquirerData: Optional[Any] = None
    merchant: Optional[Any] = None
    providerId: Optional[str] = None
    order: int
    createdAt: datetime
    updatedAt: datetime