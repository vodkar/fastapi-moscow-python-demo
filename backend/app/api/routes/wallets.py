"""Wallet management API endpoints."""

import uuid

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.crud import (
    create_wallet,
    get_user_wallets,
    get_wallet_by_id,
    get_wallet_with_transactions,
)
from app.models import (
    Wallet,
    WalletCreate,
    WalletPublic,
    WalletsPublic,
    WalletWithTransactions,
)
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/")
def read_wallets(
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> WalletsPublic:
    """Retrieve user's wallets."""
    if current_user.is_superuser:
        count_statement = select(func.count()).select_from(Wallet)
        count = session.exec(count_statement).one()
        statement = select(Wallet).offset(skip).limit(limit)
        wallet_list = session.exec(statement).all()
        wallet_data = [WalletPublic.model_validate(wallet) for wallet in wallet_list]
    else:
        user_wallets = get_user_wallets(session=session, user_id=current_user.id)
        wallet_list = user_wallets[skip : skip + limit]
        count = len(user_wallets)
        wallet_data = [WalletPublic.model_validate(wallet) for wallet in wallet_list]

    return WalletsPublic(wallet_data=wallet_data, count=count)


@router.get("/{wallet_id}")
def read_wallet(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Get wallet by ID with transactions."""
    db_wallet = get_wallet_by_id(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (db_wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    return WalletPublic.model_validate(db_wallet)


@router.get("/{wallet_id}/details")
def read_wallet_with_transactions(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletWithTransactions:
    """Get wallet by ID with transactions."""
    db_wallet = get_wallet_with_transactions(session=session, wallet_id=wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if not current_user.is_superuser and (db_wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    return WalletWithTransactions.model_validate(db_wallet)


@router.post("/")
def create_user_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create new wallet."""
    db_wallet = create_wallet(
        session=session, wallet_in=wallet_in, user_id=current_user.id
    )
    return WalletPublic.model_validate(db_wallet)
