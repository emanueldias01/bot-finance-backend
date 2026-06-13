

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List, Any

class Remuneration(BaseModel):
    indexer: str
    rateType: str
    calculation: str
    preFixedRate: float
    ratePeriodicity: str

class AvailableAmount(BaseModel):
    amount: float
    currencyCode: str
    remuneration: Remuneration

class ReservedBalance(BaseModel):
    name: str
    identification: str
    availableAmounts: List[AvailableAmount]

class BankData(BaseModel):
    transferNumber: str
    closingBalance: float
    automaticallyInvestedBalance: float
    overdraftContractedLimit: Optional[float] = None
    overdraftUsedLimit: Optional[float] = None
    unarrangedOverdraftAmount: Optional[float] = None
    hasReservedBalance: bool
    reservedBalances: List[ReservedBalance]

class CreditData(BaseModel):
    level: str
    brand: str
    balanceCloseDate: date
    balanceDueDate: date
    availableCreditLimit: float
    balanceForeignCurrency: Optional[float] = None
    minimumPayment: float
    creditLimit: float
    isLimitFlexible: bool
    holderType: str
    status: str
    disaggregatedCreditLimits: Optional[Any] = None
    additionalCards: Optional[Any] = None

class PluggyAccountResponse(BaseModel):
    id: str
    type: str
    subtype: str
    name: str
    balance: float
    currencyCode: str
    itemId: str
    number: str
    createdAt: datetime
    updatedAt: datetime
    marketingName: str
    taxNumber: str
    owner: str
    bankData: Optional[BankData] = None
    creditData: Optional[CreditData] = None