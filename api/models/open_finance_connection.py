import uuid
from sqlmodel import SQLModel, Field
from enum import Enum
from datetime import datetime

class ConnectionStatus(Enum):
    UPDATED = "UPDATED"
    LOGIN_ERROR = "LOGIN_ERROR"
    UPDATING = "UPDATING"
    OUTDATED = "OUTDATED"

class OpenFinanceConnection(SQLModel, table=True):
    __tablename__ = "open_finance_connection"
    
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False)
    pluggy_connection_id: str = Field(nullable=False)
    institution_image_url: str = Field(nullable=False)
    institution_name: str = Field(nullable=False)
    status: ConnectionStatus = Field(nullable=False)
    consent_expires_at: datetime | None = Field(default=None)
    last_updated_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default=None)

