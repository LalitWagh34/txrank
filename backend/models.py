from sqlalchemy import Column, String, Float, DateTime, Integer, Index, text
from sqlalchemy.sql import func
from database import Base
import uuid


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    idempotency_key = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
    )


class UserSummary(Base):
    """
    Denormalized summary table for O(1) reads.
    Updated atomically on every transaction write.
    """
    __tablename__ = "user_summaries"

    user_id = Column(String, primary_key=True)
    total_amount = Column(Float, nullable=False, default=0.0)
    transaction_count = Column(Integer, nullable=False, default=0)
    first_transaction_at = Column(DateTime(timezone=True), nullable=True)
    last_transaction_at = Column(DateTime(timezone=True), nullable=True)
    # Precomputed ranking score, updated on every write
    ranking_score = Column(Float, nullable=False, default=0.0)

    __table_args__ = (
        Index("idx_ranking_score", "ranking_score"),
    )