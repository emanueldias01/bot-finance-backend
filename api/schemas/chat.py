from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ChatRequestTransactions(BaseModel):
    account_id: str
    message: str


class ChatResponse(BaseModel):
    response: str

class InsightType(str, Enum):
    OPRTUNIDADE_DE_ECONOMIA = "OPORTUNIDADE_DE_ECONOMIA"
    RISCO_DE_FLUXO_DE_CAIXA = "RISCO_DE_FLUXO_DE_CAIXA"
    PADRAO_DE_GASTOS = "PADRAO_DE_GASTOS"
    DESPESA_RECORRENTE = "DESPESA_RECORRENTE"
    ALERTA = "ALERTA"
    SUGESTAO = "SUGESTAO"


class Insight(BaseModel):
    type: InsightType
    title: str
    description: str
    severity: Optional[str] = None  # LOW, MEDIUM, HIGH
    actionable: bool
    icon: str

class InsightsResponse(BaseModel):
    insights: List[Insight]
    summary: str
    has_transactions: bool = True
