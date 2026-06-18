from pydantic import BaseModel
from uuid import UUID
from datetime import datetime


class OpenFinanceItemRequest(BaseModel):
    user_id: UUID
    pluggy_connection_id: str
    institution_image_url: str
    institution_name: str
    status: str
    last_updated_at: datetime | None = None
    consent_expires_at: datetime | None = None


class OpenFinanceItemResponse(BaseModel):
    id: UUID
    user_id: UUID
    pluggy_connection_id: str
    institution_image_url: str
    institution_name: str
    status: str
    consent_expires_at: datetime | None = None
    last_updated_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None
