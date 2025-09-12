"""Wallet management API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.crud import (
    create_transaction,
    create_wallet,
    get_user_wallets,
    get_wallet_by_id,
    get_wallet_transactions,
    transfer_between_wallets,
)
from app.models import (
    Transaction,
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
    WalletCreate,
    WalletPublic,
    WalletsPublic,
    WalletTransfer,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/")
def create_user_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create a new wallet for the current user."""
    try:
        db_wallet = create_wallet(
            session=session,
            wallet_in=wallet_in,
            user_id=current_user.id,
        )
        return WalletPublic.model_validate(db_wallet)
    except ValueError as e:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(e),
        ) from e


@router.get("/")
def read_user_wallets(
    session: SessionDep,
    current_user: CurrentUser,
) -> WalletsPublic:
    """Get all wallets for the current user."""
    wallets = get_user_wallets(session=session, user_id=current_user.id)
    wallet_data = [WalletPublic.model_validate(wallet) for wallet in wallets]
    return WalletsPublic(wallet_data=wallet_data, count=len(wallet_data))


@router.get("/{wallet_id}")
def read_wallet(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Get wallet details by ID."""
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    # Check if wallet belongs to user
    if db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    return WalletPublic.model_validate(db_wallet)


@router.post("/{wallet_id}/transactions")
def create_wallet_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    transaction_in: TransactionCreate,
) -> TransactionPublic:
    """Create a new transaction for a wallet."""
    # Ensure the transaction is for the correct wallet
    if transaction_in.wallet_id != wallet_id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Transaction wallet_id must match URL parameter",
        )

    try:
        db_transaction = create_transaction(
            session=session,
            transaction_in=transaction_in,
            user_id=current_user.id,
        )
        return TransactionPublic.model_validate(db_transaction)
    except ValueError as e:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(e),
        ) from e


@router.get("/{wallet_id}/transactions")
def read_wallet_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> TransactionsPublic:
    """Get transactions for a wallet."""
    # First check if wallet exists and belongs to user
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    transactions = get_wallet_transactions(
        session=session,
        wallet_id=wallet_id,
        skip=skip,
        limit=limit,
    )

    # Get total count for pagination
    count_statement = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.wallet_id == wallet_id)
    )
    count = session.exec(count_statement).one()

    transaction_data = [
        TransactionPublic.model_validate(transaction) for transaction in transactions
    ]

    return TransactionsPublic(transaction_data=transaction_data, count=count)


@router.post("/transfer")
def transfer_between_user_wallets(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transfer: WalletTransfer,
) -> dict[str, str]:
    """Transfer money between user's wallets with currency conversion."""
    try:
        debit_transaction, credit_transaction = transfer_between_wallets(
            session=session,
            transfer=transfer,
            user_id=current_user.id,
        )
        return {
            "message": "Transfer completed successfully",
            "debit_transaction_id": str(debit_transaction.id),
            "credit_transaction_id": str(credit_transaction.id),
        }
    except ValueError as e:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(e),
        ) from e
