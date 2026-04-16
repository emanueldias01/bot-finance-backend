from pydantic import BaseModel
from uuid import UUID


class UserRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: UUID
    username: str
