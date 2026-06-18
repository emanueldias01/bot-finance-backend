from pydantic import BaseModel


class UpdateTransactionDescription(BaseModel):
    description: str
