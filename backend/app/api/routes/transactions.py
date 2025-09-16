"""Transaction management API endpoints."""

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.crud import create_transaction, get_wallet_by_id
from app.models import TransactionCreate, TransactionPublic
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/")
def create_user_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transaction_in: TransactionCreate,
) -> TransactionPublic:
    """Create new transaction."""
    # Verify the wallet belongs to the current user
    wallet = get_wallet_by_id(session=session, wallet_id=transaction_in.wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=NOT_FOUND_CODE,
            detail="Wallet not found",
        )

    if not current_user.is_superuser and (wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    db_transaction = create_transaction(session=session, transaction_in=transaction_in)
    return TransactionPublic.model_validate(db_transaction)
