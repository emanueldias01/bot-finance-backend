from pydantic import BaseModel


class TokenResponse(BaseModel):
    token: str
    email: str
    username: str
