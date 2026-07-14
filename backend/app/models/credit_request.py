from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class CreditRequestStatus(StrEnum):
    PENDING = "pendente"
    APPROVED = "aprovado"
    REJECTED = "rejeitado"


class CreditRequest(BaseModel):
    request_id: str
    cpf: str = Field(min_length=11, max_length=11)
    requested_at: datetime
    current_limit: float = Field(ge=0)
    requested_limit: float = Field(gt=0)
    status: CreditRequestStatus


class CreditRequestResult(BaseModel):
    request_id: str
    cpf: str
    current_limit: float
    requested_limit: float
    status: CreditRequestStatus
    message: str
