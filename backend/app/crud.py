"""CRUD operations for database models."""

import uuid
from typing import Final

from app.constants import BAD_REQUEST_CODE
from app.core.security import get_password_hash, verify_password
from app.models import (
    Item,
    ItemCreate,
    Transaction,
    TransactionCreate,
    User,
    UserCreate,
    UserUpdate,
    Wallet,
    WalletCreate,
)
from app.models.db_models import CurrencyType, TransactionType
from fastapi import HTTPException
from sqlmodel import Session, select


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


# Exchange rates for currency conversion (hardcoded as per requirements)
EXCHANGE_RATES: Final[dict[tuple[CurrencyType, CurrencyType], float]] = {
    (CurrencyType.USD, CurrencyType.EUR): 0.85,
    (CurrencyType.USD, CurrencyType.RUB): 75.0,
    (CurrencyType.EUR, CurrencyType.USD): 1.18,
    (CurrencyType.EUR, CurrencyType.RUB): 88.0,
    (CurrencyType.RUB, CurrencyType.USD): 0.013,
    (CurrencyType.RUB, CurrencyType.EUR): 0.011,
}

# Transaction fees for cross-currency operations (in percentage)
TRANSACTION_FEE_RATE: Final[float] = 0.02  # 2%


def get_user_wallets(*, session: Session, user_id: uuid.UUID) -> list[Wallet]:
    """Get all wallets for a user."""
    statement = select(Wallet).where(Wallet.user_id == user_id)
    return list(session.exec(statement).all())


def create_wallet(
    *, session: Session, wallet_in: WalletCreate, user_id: uuid.UUID
) -> Wallet:
    """Create a new wallet for a user."""
    # Check if user already has a wallet with this currency
    existing_wallet = session.exec(
        select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == wallet_in.currency,
        )
    ).first()

    if existing_wallet:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=f"User already has a wallet with currency {wallet_in.currency}",
        )

    # Check if user already has 3 wallets
    user_wallets = get_user_wallets(session=session, user_id=user_id)
    if len(user_wallets) >= 3:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="User cannot have more than 3 wallets",
        )

    db_wallet = Wallet.model_validate(
        wallet_in, update={"user_id": user_id, "balance": 0.0}
    )
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return db_wallet


def get_wallet_by_id(*, session: Session, wallet_id: uuid.UUID) -> Wallet | None:
    """Get wallet by ID."""
    return session.get(Wallet, wallet_id)


def get_wallet_with_transactions(
    *, session: Session, wallet_id: uuid.UUID
) -> Wallet | None:
    """Get wallet by ID with transactions loaded."""
    statement = select(Wallet).where(Wallet.id == wallet_id)
    wallet = session.exec(statement).first()
    if wallet:
        # Load transactions separately to avoid N+1 queries
        transactions = session.exec(
            select(Transaction).where(Transaction.wallet_id == wallet_id)
        ).all()
        wallet.transaction_list = list(transactions)
    return wallet


def convert_currency(
    *, amount: float, from_currency: CurrencyType, to_currency: CurrencyType
) -> tuple[float, float]:
    """Convert amount from one currency to another and calculate fee.

    Returns:
        tuple: (converted_amount, fee_amount)
    """
    if from_currency == to_currency:
        return amount, 0.0

    rate_key = (from_currency, to_currency)
    if rate_key not in EXCHANGE_RATES:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=f"Currency conversion from {from_currency} to {to_currency} not supported",
        )

    rate = EXCHANGE_RATES[rate_key]
    converted_amount = amount * rate
    fee = converted_amount * TRANSACTION_FEE_RATE
    final_amount = converted_amount - fee

    return final_amount, fee


def create_transaction(
    *, session: Session, transaction_in: TransactionCreate
) -> Transaction:
    """Create a new transaction for a wallet."""
    wallet = get_wallet_by_id(session=session, wallet_id=transaction_in.wallet_id)
    if not wallet:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Wallet not found",
        )

    # Convert amount if currencies differ
    final_amount = transaction_in.amount

    if transaction_in.currency != wallet.currency:
        final_amount, _ = convert_currency(
            amount=transaction_in.amount,
            from_currency=transaction_in.currency,
            to_currency=wallet.currency,
        )

    # Round to 2 decimal places for precision
    final_amount = round(final_amount, 2)
    wallet.balance = round(wallet.balance, 2)

    # Check balance for debit transactions
    if transaction_in.transaction_type == TransactionType.DEBIT:
        if wallet.balance < final_amount:
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail="Insufficient balance for debit transaction",
            )
        wallet.balance -= final_amount
    else:  # CREDIT
        wallet.balance += final_amount

    # Round final balance to 2 decimal places
    wallet.balance = round(wallet.balance, 2)

    # Create transaction record
    db_transaction = Transaction.model_validate(
        transaction_in,
        update={"currency": wallet.currency},  # Store in wallet's currency
    )

    session.add(db_transaction)
    session.add(wallet)  # Update wallet balance
    session.commit()
    session.refresh(db_transaction)
    session.refresh(wallet)

    return db_transaction
