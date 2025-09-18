"""Transaction management API endpoints."""

import uuid

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, CREATED_CODE, NOT_FOUND_CODE
from app.crud import create_transaction, get_wallet_by_id, get_wallet_transactions
from app.models import TransactionCreate, TransactionPublic, TransactionsPublic
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/", status_code=CREATED_CODE)
def create_wallet_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transaction_in: TransactionCreate,
) -> TransactionPublic:
    """Create a new transaction for a wallet."""
    # Verify that the wallet belongs to the current user
    wallet = get_wallet_by_id(session=session, wallet_id=transaction_in.wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    try:
        db_transaction = create_transaction(
            session=session, transaction_in=transaction_in
        )
        return TransactionPublic.model_validate(db_transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(e),
        ) from e


@router.get("/wallet/{wallet_id}")
def read_wallet_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> TransactionsPublic:
    """Get all transactions for a specific wallet."""
    # Verify that the wallet belongs to the current user
    wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    transaction_list = get_wallet_transactions(session=session, wallet_id=wallet_id)
    transaction_data = [
        TransactionPublic.model_validate(transaction)
        for transaction in transaction_list
    ]
    return TransactionsPublic(
        transaction_data=transaction_data, count=len(transaction_data)
    )
