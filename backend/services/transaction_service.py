from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.exc import IntegrityError
from datetime import datetime, timezone
from models import Transaction, UserSummary
from schemas import TransactionRequest, TransactionResponse
from services.ranking_service import compute_ranking_score
import uuid


async def process_transaction(
    db: AsyncSession,
    payload: TransactionRequest,
) -> TransactionResponse:
    """
    Idempotent transaction processor.

    Flow:
      1. Try to insert the transaction row (unique idempotency_key constraint).
      2. If INSERT succeeds → upsert the user summary atomically.
      3. If INSERT fails with IntegrityError → duplicate; return the original.

    Concurrency: SQLite WAL mode + SQLAlchemy async ensures that two simultaneous
    requests with the same idempotency_key will race to INSERT; only one wins,
    the other gets IntegrityError and returns the stored record safely.
    """
    # --- 1. Attempt idempotent insert ---
    tx = Transaction(
        id=str(uuid.uuid4()),
        idempotency_key=payload.idempotency_key,
        user_id=payload.user_id,
        amount=payload.amount,
        description=payload.description,
    )

    try:
        db.add(tx)
        await db.flush()  # triggers constraint check without committing
    except IntegrityError:
        await db.rollback()
        # Return the existing transaction for this idempotency key
        existing = await db.scalar(
            select(Transaction).where(
                Transaction.idempotency_key == payload.idempotency_key
            )
        )
        return TransactionResponse(
            id=existing.id,
            user_id=existing.user_id,
            amount=existing.amount,
            description=existing.description,
            idempotency_key=existing.idempotency_key,
            created_at=existing.created_at,
            was_duplicate=True,
        )

    # --- 2. Upsert user summary (atomic aggregate update) ---
    now = datetime.now(timezone.utc)

    # Fetch current system maxima for score normalisation
    max_vals = await db.execute(
        select(
            func.max(UserSummary.total_amount),
            func.max(UserSummary.transaction_count),
        )
    )
    max_amount, max_count = max_vals.one()
    max_amount = max(max_amount or 0.0, payload.amount)
    max_count = max(max_count or 0, 1)

    # Check if summary row exists
    summary = await db.get(UserSummary, payload.user_id)

    if summary is None:
        new_score = compute_ranking_score(
            payload.amount, 1, now, max_amount, max_count
        )
        summary = UserSummary(
            user_id=payload.user_id,
            total_amount=payload.amount,
            transaction_count=1,
            first_transaction_at=now,
            last_transaction_at=now,
            ranking_score=new_score,
        )
        db.add(summary)
    else:
        new_total = summary.total_amount + payload.amount
        new_count = summary.transaction_count + 1
        new_score = compute_ranking_score(
            new_total, new_count, now, max(max_amount, new_total), max(max_count, new_count)
        )
        await db.execute(
            update(UserSummary)
            .where(UserSummary.user_id == payload.user_id)
            .values(
                total_amount=new_total,
                transaction_count=new_count,
                last_transaction_at=now,
                ranking_score=new_score,
            )
        )

    # --- 3. Recompute all other users' scores (normalisation changed) ---
    # In production this would be a background job; here we do it inline for correctness.
    await _renormalise_all_scores(db)

    await db.commit()
    await db.refresh(tx)

    return TransactionResponse(
        id=tx.id,
        user_id=tx.user_id,
        amount=tx.amount,
        description=tx.description,
        idempotency_key=tx.idempotency_key,
        created_at=tx.created_at,
        was_duplicate=False,
    )


async def _renormalise_all_scores(db: AsyncSession) -> None:
    """
    After any write, recompute every user's ranking score so normalisation
    stays consistent across the whole leaderboard.
    """
    max_vals = await db.execute(
        select(
            func.max(UserSummary.total_amount),
            func.max(UserSummary.transaction_count),
        )
    )
    max_amount, max_count = max_vals.one()
    if not max_amount:
        return

    summaries = (await db.execute(select(UserSummary))).scalars().all()
    for s in summaries:
        score = compute_ranking_score(
            s.total_amount,
            s.transaction_count,
            s.last_transaction_at,
            max_amount,
            max_count,
        )
        s.ranking_score = score