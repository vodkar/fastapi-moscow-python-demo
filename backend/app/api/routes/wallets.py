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
    WalletTransferCreate,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/")
def create_user_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create new wallet for the current user."""
    try:
        db_wallet = create_wallet(
            session=session, wallet_in=wallet_in, user_id=current_user.id
        )
        return WalletPublic.model_validate(db_wallet)
    except ValueError as error:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(error),
        ) from error


@router.get("/")
def read_user_wallets(
    session: SessionDep,
    current_user: CurrentUser,
) -> WalletsPublic:
    """Retrieve current user's wallets."""
    wallet_list = get_user_wallets(session=session, user_id=current_user.id)
    wallet_public_list = [WalletPublic.model_validate(wallet) for wallet in wallet_list]
    return WalletsPublic(wallet_data=wallet_public_list, count=len(wallet_public_list))


@router.get("/{wallet_id}")
def read_wallet(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Get wallet by ID."""
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
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
    """Create new transaction for a wallet."""
    # Get the wallet and validate ownership
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    # Ensure transaction wallet_id matches the URL parameter
    transaction_data = transaction_in.model_copy(update={"wallet_id": wallet_id})

    try:
        db_transaction = create_transaction(
            session=session,
            transaction_in=transaction_data,
            wallet=db_wallet,
        )
        return TransactionPublic.model_validate(db_transaction)
    except ValueError as error:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(error),
        ) from error


@router.get("/{wallet_id}/transactions")
def read_wallet_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> TransactionsPublic:
    """Get transactions for a wallet."""
    # Validate wallet ownership
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    transaction_list = get_wallet_transactions(
        session=session,
        wallet_id=wallet_id,
        skip=skip,
        limit=limit,
    )

    # Get total count
    count_statement = (
        select(func.count())
        .select_from(Transaction)
        .where(Transaction.wallet_id == wallet_id)
    )
    count = session.exec(count_statement).one()

    transaction_public_list = [
        TransactionPublic.model_validate(t) for t in transaction_list
    ]
    return TransactionsPublic(transaction_data=transaction_public_list, count=count)


@router.post("/transfer")
def transfer_funds(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transfer_in: WalletTransferCreate,
) -> dict[str, list[TransactionPublic]]:
    """Transfer funds between user's wallets."""
    try:
        debit_transaction, credit_transaction = transfer_between_wallets(
            session=session,
            transfer_in=transfer_in,
            user_id=current_user.id,
        )
        return {
            "transactions": [
                TransactionPublic.model_validate(debit_transaction),
                TransactionPublic.model_validate(credit_transaction),
            ]
        }
    except ValueError as error:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=str(error),
        ) from error
