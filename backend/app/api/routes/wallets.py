"""Wallet and transaction API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.models import (
    TransactionCreate,
    TransactionPublic,
    Wallet,
    WalletCreate,
    WalletPublic,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/")
def create_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create a new wallet for current user."""
    try:
        wallet = crud.create_wallet(
            session=session,
            wallet_in=wallet_in,
            owner_id=current_user.id,
        )
    except ValueError as exc:  # pragma: no cover - simple mapping
        raise HTTPException(status_code=BAD_REQUEST_CODE, detail=str(exc)) from exc
    return WalletPublic.model_validate(wallet)


@router.get("/{wallet_id}")
def get_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Retrieve wallet by ID."""
    wallet = session.get(Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if wallet.owner_id != current_user.id and (not current_user.is_superuser):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    return WalletPublic.model_validate(wallet)


@router.post("/{wallet_id}/transactions")
def create_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    transaction_in: TransactionCreate,
) -> TransactionPublic:
    """Create a transaction (credit/debit)."""
    wallet = session.get(Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if wallet.owner_id != current_user.id and (not current_user.is_superuser):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    try:
        tx = crud.create_transaction(
            session=session,
            wallet=wallet,
            tx_in=transaction_in,
        )
    except ValueError as exc:  # business rule violation
        raise HTTPException(status_code=BAD_REQUEST_CODE, detail=str(exc)) from exc
    return TransactionPublic.model_validate(tx)
