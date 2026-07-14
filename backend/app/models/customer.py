from datetime import date

from pydantic import BaseModel, Field


class Customer(BaseModel):
    cpf: str = Field(min_length=11, max_length=11)
    name: str
    birth_date: date
    credit_score: int = Field(ge=0, le=1000)
    credit_limit: float = Field(ge=0)