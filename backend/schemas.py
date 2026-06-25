from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import datetime
import uuid
import re


class TransactionRequest(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=64)
    amount: float = Field(..., gt=0, le=1_000_000)
    description: Optional[str] = Field(None, max_length=256)
    # Client-supplied idempotency key; if omitted, we generate one
    idempotency_key: Optional[str] = Field(None, max_length=128)

    @field_validator("user_id")
    @classmethod
    def user_id_alphanumeric(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_\-]+$", v):
            raise ValueError("user_id must be alphanumeric (underscores and hyphens allowed)")
        return v.lower()

    @field_validator("amount")
    @classmethod
    def amount_precision(cls, v: float) -> float:
        # Limit to 2 decimal places to prevent floating-point manipulation
        return round(v, 2)

    @model_validator(mode="after")
    def ensure_idempotency_key(self) -> "TransactionRequest":
        if not self.idempotency_key:
            self.idempotency_key = str(uuid.uuid4())
        return self


class TransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: float
    description: Optional[str]
    idempotency_key: str
    created_at: datetime
    was_duplicate: bool = False


class SummaryResponse(BaseModel):
    user_id: str
    total_amount: float
    transaction_count: int
    average_transaction: float
    first_transaction_at: Optional[datetime]
    last_transaction_at: Optional[datetime]
    ranking_score: float
    rank: Optional[int]


class RankedUser(BaseModel):
    rank: int
    user_id: str
    total_amount: float
    transaction_count: int
    ranking_score: float
    last_transaction_at: Optional[datetime]


class RankingResponse(BaseModel):
    users: list[RankedUser]
    total_users: int
    scoring_formula: str