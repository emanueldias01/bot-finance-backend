from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class PayableRequest(BaseModel):
    description: str
    category: str
    value: float
    due_date: datetime
    status: str = "pending"


class PayableResponse(BaseModel):
    id: UUID
    description: str
    category: str
    value: float
    due_date: datetime
    status: str
    created_at: datetime


class ReceivableRequest(BaseModel):
    client: str
    value: float
    forecast_date: datetime
    status: str = "pending"


class ReceivableResponse(BaseModel):
    id: UUID
    client: str
    value: float
    forecast_date: datetime
    status: str
    created_at: datetime
