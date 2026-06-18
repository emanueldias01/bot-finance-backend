from pydantic import BaseModel


class ChatRequestTransactions(BaseModel):
    account_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
