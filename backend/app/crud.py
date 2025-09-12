"""CRUD operations for database models including wallet & transactions."""

import uuid
from collections.abc import Iterable
from decimal import Decimal

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    AVAILABLE_CURRENCIES,
    Item,
    ItemCreate,
    Transaction,
    TransactionCreate,
    TransactionType,
    User,
    UserCreate,
    UserUpdate,
    Wallet,
    WalletCreate,
)

# Fixed exchange rates base USD
_EXCHANGE_RATES: dict[str, Decimal] = {
    "USD": Decimal(1),
    "EUR": Decimal("0.9"),
    "RUB": Decimal(90),
}

_FEE_PERCENT = Decimal("0.01")  # 1% fee on cross-currency conversions


def _convert(amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
    """Convert amount between currencies using fixed rates.

    Rates specify 1 USD => rate units.
    Conversion: amount_in_usd = amount / rate_from then * rate_to.
    """
    if from_currency == to_currency:
        return amount
    rate_from = _EXCHANGE_RATES[from_currency]
    rate_to = _EXCHANGE_RATES[to_currency]
    usd_amount = amount / rate_from
    target_amount = usd_amount * rate_to
    # Apply fee on cross-currency
    fee = target_amount * _FEE_PERCENT
    return (target_amount - fee).quantize(Decimal("0.01"))


def create_user(*, session: Session, user_create: UserCreate) -> User:
    """Create a new user."""
    db_obj = User.model_validate(
        user_create,
        update={"hashed_password": get_password_hash(user_create.password)},
    )
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> User:
    """Update an existing user."""
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if password := user_data.get("password"):
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_email(*, session: Session, email: str) -> User | None:
    """Get user by email address."""
    statement = select(User).where(User.email == email)
    return session.exec(statement).first()


def authenticate(*, session: Session, email: str, password: str) -> User | None:
    """Authenticate user with email and password."""
    db_user = get_user_by_email(session=session, email=email)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    """Create a new item."""
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item


# ---------------- Wallet CRUD ----------------


def get_user_wallets(session: Session, user_id: uuid.UUID) -> list[Wallet]:
    """Return wallets for a user."""
    statement = select(Wallet).where(Wallet.owner_id == user_id)
    return list(session.exec(statement).all())


MAX_WALLETS_PER_USER = 3


def create_wallet(
    *,
    session: Session,
    wallet_in: WalletCreate,
    owner_id: uuid.UUID,
) -> Wallet:
    """Create wallet for a user; enforce max wallets and unique currency per user."""
    existing_wallets = get_user_wallets(session, owner_id)
    if len(existing_wallets) >= MAX_WALLETS_PER_USER:
        msg = "User already has maximum number of wallets"
        raise ValueError(msg)
    if any(w.currency == wallet_in.currency for w in existing_wallets):
        msg = "Wallet with this currency already exists"
        raise ValueError(msg)
    db_wallet = Wallet.model_validate(wallet_in, update={"owner_id": owner_id})
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return db_wallet


def get_wallet(session: Session, wallet_id: uuid.UUID) -> Wallet | None:
    """Get wallet by id."""
    return session.get(Wallet, wallet_id)


# ---------------- Transaction CRUD ----------------


def create_transaction(
    *,
    session: Session,
    wallet: Wallet,
    tx_in: TransactionCreate,
) -> Transaction:
    """Create a transaction and update wallet balance with rules.

    If tx currency differs from wallet currency, convert.
    Debit cannot overdraw wallet.
    """
    amount = tx_in.amount
    if tx_in.currency not in AVAILABLE_CURRENCIES:
        msg = "Unsupported currency"
        raise ValueError(msg)
    if tx_in.type == TransactionType.CREDIT:
        # Convert if needed
        final_amount = _convert(amount, tx_in.currency, wallet.currency)
        wallet.balance = (wallet.balance + final_amount).quantize(Decimal("0.01"))
    else:  # debit
        # Amount to subtract after conversion from provided currency to wallet currency
        final_amount = _convert(amount, tx_in.currency, wallet.currency)
        new_balance = (wallet.balance - final_amount).quantize(Decimal("0.01"))
        if new_balance < Decimal("0.00"):
            msg = "Insufficient funds"
            raise ValueError(msg)
        wallet.balance = new_balance

    tx = Transaction.model_validate(
        tx_in,
        update={"wallet_id": wallet.id, "amount": amount},  # store original amount
    )
    session.add(wallet)
    session.add(tx)
    session.commit()
    session.refresh(wallet)
    session.refresh(tx)
    return tx


def list_transactions(
    session: Session,
    wallet_id: uuid.UUID,
    limit: int = 100,
    skip: int = 0,
) -> Iterable[Transaction]:
    """List transactions for a wallet."""
    statement = (
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .offset(skip)
        .limit(limit)
    )
    return session.exec(statement).all()
