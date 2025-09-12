"""Transaction API endpoints."""

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.models import (
    Transaction,
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    Wallet,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/")
def create_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    tx_in: TransactionCreate,
) -> TransactionPublic:
    """Create a transaction for a wallet owned by the user (or any if superuser)."""
    wallet = session.get(Wallet, tx_in.wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    try:
        tx = crud.create_transaction(session=session, tx_in=tx_in)
    except ValueError as exc:  # noqa: WPS329
        raise HTTPException(status_code=BAD_REQUEST_CODE, detail=str(exc)) from exc
    return TransactionPublic.model_validate(tx)


@router.get("/wallet/{wallet_id}")
def list_wallet_transactions(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: str,
) -> TransactionsPublic:
    """List transactions for a wallet."""
    wallet = session.get(Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    count = session.exec(
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.wallet_id == wallet_id),
    ).one()
    tx_list = session.exec(
        select(Transaction).where(Transaction.wallet_id == wallet_id),
    ).all()
    public_list = [TransactionPublic.model_validate(t) for t in tx_list]
    return TransactionsPublic(transaction_data=public_list, count=count)
