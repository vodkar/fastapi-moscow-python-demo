"""Wallet management API endpoints."""

import uuid

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app import crud
from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.models import Wallet, WalletCreate, WalletPublic, WalletsPublic

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.get("/")
def list_wallets(
    session: SessionDep,
    current_user: CurrentUser,
) -> WalletsPublic:
    """List current user's wallets (superuser sees all)."""
    if current_user.is_superuser:
        count = session.exec(select(func.count()).select_from(Wallet)).one()
        wallet_list = session.exec(select(Wallet)).all()
    else:
        count = session.exec(
            select(func.count())
            .select_from(Wallet)
            .where(Wallet.user_id == current_user.id),
        ).one()
        wallet_list = session.exec(
            select(Wallet).where(Wallet.user_id == current_user.id),
        ).all()
    public_list = [WalletPublic.model_validate(w) for w in wallet_list]
    return WalletsPublic(wallet_data=public_list, count=count)


@router.post("/")
def create_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create a new wallet for the current user."""
    try:
        wallet = crud.create_wallet(
            session=session,
            user_id=current_user.id,
            wallet_in=wallet_in,
        )
    except ValueError as exc:  # noqa: WPS329
        raise HTTPException(status_code=BAD_REQUEST_CODE, detail=str(exc)) from exc
    return WalletPublic.model_validate(wallet)


@router.get("/{wallet_id}")
def get_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Get wallet details."""
    wallet = session.get(Wallet, wallet_id)
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    return WalletPublic.model_validate(wallet)
