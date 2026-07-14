from pydantic import BaseModel, Field


class ScoreLimitRange(BaseModel):
    minimum_score: int = Field(ge=0, le=1000)
    maximum_score: int = Field(ge=0, le=1000)
    maximum_credit_limit: float = Field(ge=0)


class ScoreUpdateResult(BaseModel):
    previous_score: int = Field(ge=0, le=1000)
    new_score: int = Field(ge=0, le=1000)