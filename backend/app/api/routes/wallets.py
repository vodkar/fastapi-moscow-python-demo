"""Wallet management API endpoints."""

import uuid

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, CREATED_CODE, NOT_FOUND_CODE
from app.crud import create_wallet, get_user_wallets, get_wallet_by_id
from app.models import Message, WalletCreate, WalletPublic, WalletsPublic
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/", status_code=CREATED_CODE)
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
    """Retrieve all wallets for the current user."""
    wallet_list = get_user_wallets(session=session, user_id=current_user.id)
    wallet_data = [WalletPublic.model_validate(wallet) for wallet in wallet_list]
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

    # Check if wallet belongs to current user or user is superuser
    if not current_user.is_superuser and (db_wallet.user_id != current_user.id):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )

    return WalletPublic.model_validate(db_wallet)
