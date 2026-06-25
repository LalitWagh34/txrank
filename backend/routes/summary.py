from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import UserSummary
from schemas import SummaryResponse

router = APIRouter()


@router.get("/summary/{user_id}", response_model=SummaryResponse)
async def get_user_summary(user_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns aggregated stats and current rank for a user.
    Rank is computed live by counting users with a higher score.
    """
    user_id = user_id.lower()
    summary = await db.get(UserSummary, user_id)

    if summary is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found.")

    # Rank = number of users with strictly higher score + 1
    rank_result = await db.scalar(
        select(func.count()).where(UserSummary.ranking_score > summary.ranking_score)
    )
    rank = (rank_result or 0) + 1

    avg = summary.total_amount / summary.transaction_count if summary.transaction_count else 0.0

    return SummaryResponse(
        user_id=summary.user_id,
        total_amount=round(summary.total_amount, 2),
        transaction_count=summary.transaction_count,
        average_transaction=round(avg, 2),
        first_transaction_at=summary.first_transaction_at,
        last_transaction_at=summary.last_transaction_at,
        ranking_score=summary.ranking_score,
        rank=rank,
    )