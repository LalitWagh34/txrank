"""
Ranking Score Formula
---------------------
score = (normalized_amount * 0.5)
      + (normalized_frequency * 0.3)
      + (recency_score * 0.2)

Where:
  normalized_amount    = user_total / max_total_in_system   (rewards high spenders)
  normalized_frequency = user_tx_count / max_tx_count       (rewards consistent users)
  recency_score        = exp(-days_since_last_tx / 30)      (decays over 30-day half-life)

All three components are in [0, 1], so the final score is also in [0, 1].

Abuse prevention:
  - A single massive transaction doesn't dominate because amount is only 50% weight.
  - Recency decay means old bulk uploads don't hold rank forever.
  - Normalization means rankings are relative, not gameable by absolute numbers.
"""

import math
from datetime import datetime, timezone
from typing import Optional


WEIGHT_AMOUNT = 0.50
WEIGHT_FREQUENCY = 0.30
WEIGHT_RECENCY = 0.20
RECENCY_HALF_LIFE_DAYS = 30


def compute_recency_score(last_transaction_at: Optional[datetime]) -> float:
    """Exponential decay: score=1.0 if just now, approaches 0 over time."""
    if last_transaction_at is None:
        return 0.0
    now = datetime.now(timezone.utc)
    # Make sure last_transaction_at is tz-aware
    if last_transaction_at.tzinfo is None:
        last_transaction_at = last_transaction_at.replace(tzinfo=timezone.utc)
    days_elapsed = (now - last_transaction_at).total_seconds() / 86400
    return math.exp(-days_elapsed / RECENCY_HALF_LIFE_DAYS)


def compute_ranking_score(
    total_amount: float,
    transaction_count: int,
    last_transaction_at: Optional[datetime],
    max_amount: float,
    max_count: int,
) -> float:
    """
    Compute a normalised [0, 1] ranking score.
    Handles edge cases where max values are 0 (first user).
    """
    norm_amount = (total_amount / max_amount) if max_amount > 0 else 0.0
    norm_freq = (transaction_count / max_count) if max_count > 0 else 0.0
    recency = compute_recency_score(last_transaction_at)

    score = (
        WEIGHT_AMOUNT * norm_amount
        + WEIGHT_FREQUENCY * norm_freq
        + WEIGHT_RECENCY * recency
    )
    return round(score, 6)


SCORING_FORMULA = (
    "score = 0.50 × (user_total / max_total) "
    "+ 0.30 × (user_tx_count / max_tx_count) "
    "+ 0.20 × exp(−days_since_last_tx / 30)"
)