from decimal import Decimal
from uuid import UUID

from app.models import Currency, Wallet
from app.tests.utils.user import create_random_user
from sqlmodel import Session


def create_random_wallet(
    db: Session, *, user_id: UUID | None = None, currency: Currency = Currency.USD
) -> Wallet:
    """Create a random wallet for testing."""
    if user_id is None:
        user = create_random_user(db)
        user_id = user.id

    wallet = Wallet(
        user_id=user_id,
        balance=0.0,
        currency=currency,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet


def create_wallet_with_balance(
    db: Session,
    *,
    user_id: UUID | None = None,
    currency: Currency = Currency.USD,
    balance: float = 100.0,
) -> Wallet:
    """Create a wallet with a specific balance for testing."""
    if user_id is None:
        user = create_random_user(db)
        user_id = user.id

    wallet = Wallet(
        user_id=user_id,
        balance=balance,
        currency=currency,
    )
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet
