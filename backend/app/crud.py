"""CRUD operations for database models."""

import uuid
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    ALLOWED_CURRENCIES,
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


# ---- Wallet & Transaction helpers ----


def _quantize(amount: Decimal) -> Decimal:
    """Round decimal to 2 places using bankers rounding policy."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# Simplistic fixed exchange rates relative to USD
EXCHANGE_RATES: dict[tuple[str, str], Decimal] = {
    ("USD", "EUR"): Decimal("0.90"),
    ("EUR", "USD"): Decimal("1.11"),
    ("USD", "RUB"): Decimal(90),
    ("RUB", "USD"): Decimal("0.0111"),
    ("EUR", "RUB"): Decimal(100),
    ("RUB", "EUR"): Decimal("0.01"),
}

FEE_RATE = Decimal("0.01")  # 1% fee on cross-currency transactions
MAX_WALLETS_PER_USER = 3


def create_wallet(
    *,
    session: Session,
    user_id: uuid.UUID,
    wallet_in: WalletCreate,
) -> Wallet:
    """Create wallet ensuring limits and currency uniqueness per user."""
    # Ensure valid currency
    if wallet_in.currency not in ALLOWED_CURRENCIES:
        msg = "Unsupported currency"
        raise ValueError(msg)

    # A user can have up to 3 wallets.
    existing_wallets = session.query(Wallet).filter(Wallet.user_id == user_id).all()  # type: ignore[attr-defined]
    if len(existing_wallets) >= MAX_WALLETS_PER_USER:
        msg = "Maximum number of wallets reached"
        raise ValueError(msg)
    # Prevent duplicate currency wallet for same user
    if any(w.currency == wallet_in.currency for w in existing_wallets):
        msg = "Wallet for currency already exists"
        raise ValueError(msg)

    db_wallet = Wallet.model_validate(wallet_in, update={"user_id": user_id})
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return db_wallet


def _convert(amount: Decimal, src: str, dst: str) -> Decimal:
    if src == dst:
        return amount
    rate = EXCHANGE_RATES.get((src, dst))
    if rate is None:
        msg = "Conversion rate not defined"
        raise ValueError(msg)
    return _quantize(amount * rate)


def create_transaction(
    *,
    session: Session,
    tx_in: TransactionCreate,
) -> Transaction:
    """Create a transaction adjusting wallet balance with validation.

    For cross-currency (transaction currency different than wallet currency),
    amount is converted and fee applied before crediting/debiting wallet.
    """
    wallet = session.get(Wallet, tx_in.wallet_id)
    if not wallet:
        msg = "Wallet not found"
        raise ValueError(msg)

    raw_amount = Decimal(str(tx_in.amount))
    amount = _quantize(raw_amount)

    # Convert if different currency
    effective_amount = amount
    if tx_in.currency != wallet.currency:
        converted = _convert(amount, tx_in.currency, wallet.currency)
        fee = _quantize(converted * FEE_RATE)
        # Fee always deducted (for credit reduces incoming, for debit increases outgoing)
        if tx_in.type == TransactionType.credit:
            effective_amount = converted - fee
        else:  # debit
            effective_amount = converted + fee
    # Apply credit/debit
    new_balance = wallet.balance
    if tx_in.type == TransactionType.credit:
        new_balance = _quantize(wallet.balance + effective_amount)
    else:  # debit
        if wallet.balance < effective_amount:
            msg = "Insufficient balance"
            raise ValueError(msg)
        new_balance = _quantize(wallet.balance - effective_amount)

    wallet.balance = new_balance
    session.add(wallet)
    db_tx = Transaction.model_validate(
        tx_in,
        update={
            "amount": amount,  # original amount in tx currency
        },
    )
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return db_tx
