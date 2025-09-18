"""CRUD operations for database models."""

import uuid
from typing import Any

from app.core.security import get_password_hash, verify_password
from app.models import (
    Currency,
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
from sqlmodel import Session, desc, func, select


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


# Exchange rates for currency conversion (hardcoded for simplicity)
EXCHANGE_RATES = {
    ("USD", "EUR"): 0.85,
    ("USD", "RUB"): 75.0,
    ("EUR", "USD"): 1.18,
    ("EUR", "RUB"): 88.0,
    ("RUB", "USD"): 0.013,
    ("RUB", "EUR"): 0.011,
}

# Transaction fee percentage
TRANSACTION_FEE = 0.02  # 2%


def get_exchange_rate(from_currency: Currency, to_currency: Currency) -> float:
    """Get exchange rate between two currencies."""
    if from_currency == to_currency:
        return 1.0
    return EXCHANGE_RATES.get((from_currency.value, to_currency.value), 1.0)


def create_wallet(
    *, session: Session, wallet_in: WalletCreate, user_id: uuid.UUID
) -> Wallet:
    """Create a new wallet for a user."""
    # Check if user already has a wallet with this currency
    existing_wallet = session.exec(
        select(Wallet).where(
            Wallet.user_id == user_id, Wallet.currency == wallet_in.currency
        )
    ).first()

    if existing_wallet:
        raise ValueError(
            f"User already has a wallet with currency {wallet_in.currency.value}"
        )

    # Check if user already has 3 wallets
    wallet_count = session.exec(
        select(func.count()).select_from(Wallet).where(Wallet.user_id == user_id)
    ).one()

    if wallet_count >= 3:
        raise ValueError("User can have a maximum of 3 wallets")

    db_wallet = Wallet.model_validate(wallet_in, update={"user_id": user_id})
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return db_wallet


def get_wallet_by_id(*, session: Session, wallet_id: uuid.UUID) -> Wallet | None:
    """Get wallet by ID."""
    return session.get(Wallet, wallet_id)


def get_user_wallets(*, session: Session, user_id: uuid.UUID) -> list[Wallet]:
    """Get all wallets for a user."""
    statement = select(Wallet).where(Wallet.user_id == user_id)
    return list(session.exec(statement).all())


def create_transaction(
    *, session: Session, transaction_in: TransactionCreate
) -> Transaction:
    """Create a new transaction and update wallet balance."""
    # Get the wallet
    wallet = session.get(Wallet, transaction_in.wallet_id)
    if not wallet:
        raise ValueError("Wallet not found")

    # Validate currency compatibility or handle conversion
    amount_in_wallet_currency = transaction_in.amount
    fee = 0.0

    if transaction_in.currency != wallet.currency:
        # Convert currency and apply fee
        exchange_rate = get_exchange_rate(transaction_in.currency, wallet.currency)
        amount_in_wallet_currency = round(transaction_in.amount * exchange_rate, 2)
        fee = round(amount_in_wallet_currency * TRANSACTION_FEE, 2)
        amount_in_wallet_currency -= fee

    # Check balance for debit transactions
    if transaction_in.type == TransactionType.DEBIT:
        if wallet.balance < amount_in_wallet_currency:
            raise ValueError("Insufficient balance for debit transaction")
        new_balance = round(wallet.balance - amount_in_wallet_currency, 2)
    else:  # CREDIT
        new_balance = round(wallet.balance + amount_in_wallet_currency, 2)

    # Update wallet balance
    wallet.balance = new_balance
    session.add(wallet)

    # Create transaction record
    db_transaction = Transaction.model_validate(transaction_in)
    session.add(db_transaction)

    session.commit()
    session.refresh(db_transaction)
    return db_transaction


def get_wallet_transactions(
    *, session: Session, wallet_id: uuid.UUID
) -> list[Transaction]:
    """Get all transactions for a wallet."""
    statement = (
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(desc(Transaction.timestamp))
    )
    return list(session.exec(statement).all())
