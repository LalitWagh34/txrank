from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from database import get_db
from models import UserSummary
from schemas import RankedUser, RankingResponse
from services.ranking_service import SCORING_FORMULA

router = APIRouter()


@router.get("/ranking", response_model=RankingResponse)
async def get_ranking(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns paginated leaderboard sorted by ranking_score DESC.
    Ties broken by total_amount DESC, then transaction_count DESC.
    """
    total = await db.scalar(select(func.count()).select_from(UserSummary))

    rows = (
        await db.execute(
            select(UserSummary)
            .order_by(
                UserSummary.ranking_score.desc(),
                UserSummary.total_amount.desc(),
                UserSummary.transaction_count.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
    ).scalars().all()

    ranked = [
        RankedUser(
            rank=offset + idx + 1,
            user_id=row.user_id,
            total_amount=round(row.total_amount, 2),
            transaction_count=row.transaction_count,
            ranking_score=row.ranking_score,
            last_transaction_at=row.last_transaction_at,
        )
        for idx, row in enumerate(rows)
    ]

    return RankingResponse(
        users=ranked,
        total_users=total or 0,
        scoring_formula=SCORING_FORMULA,
    )