"""Transaction management API endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.crud import create_transaction, get_wallet_by_id, get_wallet_transactions
from app.models import (
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    TransactionTypeEnum,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreateWithTarget(BaseModel):
    """Transaction creation model with optional target wallet for transfers."""

    wallet_id: uuid.UUID
    amount: Decimal
    transaction_type: TransactionTypeEnum
    target_wallet_id: uuid.UUID | None = None


@router.get("/wallet/{wallet_id}")
def read_wallet_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> TransactionsPublic:
    """Retrieve transactions for a wallet."""
    # Verify wallet ownership
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (db_wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    transaction_list = get_wallet_transactions(session=session, wallet_id=wallet_id)
    transaction_public_list = [
        TransactionPublic.model_validate(transaction)
        for transaction in transaction_list
    ]
    return TransactionsPublic(
        transaction_data=transaction_public_list, count=len(transaction_public_list)
    )


@router.post("/")
def create_wallet_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transaction_in: TransactionCreateWithTarget,
) -> TransactionPublic:
    """Create new transaction for a wallet."""
    # Verify wallet ownership
    db_wallet = get_wallet_by_id(session=session, wallet_id=transaction_in.wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (db_wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    # Verify target wallet ownership if provided
    if transaction_in.target_wallet_id:
        target_wallet = get_wallet_by_id(
            session=session, wallet_id=transaction_in.target_wallet_id
        )
        if not target_wallet:
            raise HTTPException(
                status_code=NOT_FOUND_CODE, detail="Target wallet not found"
            )

        if not current_user.is_superuser and (target_wallet.user_id != current_user.id):
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail="Not enough permissions for target wallet",
            )

    # Convert to proper TransactionCreate model
    transaction_create = TransactionCreate(
        wallet_id=transaction_in.wallet_id,
        amount=transaction_in.amount,
        transaction_type=transaction_in.transaction_type,
    )

    try:
        db_transaction = create_transaction(
            session=session,
            transaction_in=transaction_create,
            target_wallet_id=transaction_in.target_wallet_id,
        )
        return TransactionPublic.model_validate(db_transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(e),
        )
