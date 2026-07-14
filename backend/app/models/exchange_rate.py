from datetime import datetime

from pydantic import BaseModel, Field


class ExchangeRate(BaseModel):
    source_currency: str = Field(min_length=3, max_length=3)
    target_currency: str = Field(min_length=3, max_length=3)
    rate: float = Field(gt=0)
    consulted_at: datetime