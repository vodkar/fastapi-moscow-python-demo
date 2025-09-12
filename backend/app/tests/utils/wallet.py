from sqlmodel import Session

from app import crud
from app.models import Wallet, WalletCreate
from app.tests.utils.user import create_random_user


def create_wallet(db: Session, currency: str = "USD") -> Wallet:
    user = create_random_user(db)
    wallet_in = WalletCreate(currency=currency)
    return crud.create_wallet(session=db, user_id=user.id, wallet_in=wallet_in)
