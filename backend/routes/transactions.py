from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from schemas import TransactionRequest, TransactionResponse
from services.transaction_service import process_transaction

router = APIRouter()


@router.post("/transaction", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    payload: TransactionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Submit a financial transaction.

    - amount must be > 0 and ≤ 1,000,000
    - user_id must be alphanumeric
    - Provide an idempotency_key to safely retry without double-processing.
      If omitted, one is auto-generated (non-retryable).
    - Returns was_duplicate=true if the key was already processed.
    """
    try:
        result = await process_transaction(db, payload)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))