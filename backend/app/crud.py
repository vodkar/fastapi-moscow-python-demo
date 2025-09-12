"""CRUD operations for database models."""

import uuid
from decimal import Decimal

from sqlmodel import Session, select

from app.constants import MAX_WALLETS_PER_USER
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
    WalletTransfer,
)
from app.utils import convert_with_fee


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


# Wallet CRUD operations
def create_wallet(
    *, session: Session, wallet_in: WalletCreate, user_id: uuid.UUID
) -> Wallet:
    """Create a new wallet for a user."""
    # Check if user already has a wallet with this currency
    existing_wallet = session.exec(
        select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == wallet_in.currency,
        ),
    ).first()

    if existing_wallet:
        error_msg = f"User already has a {wallet_in.currency} wallet"
        raise ValueError(error_msg)

    # Check if user already has maximum wallets
    wallet_count = session.exec(
        select(Wallet).where(Wallet.user_id == user_id),
    ).all()

    if len(wallet_count) >= MAX_WALLETS_PER_USER:
        error_msg = f"User cannot have more than {MAX_WALLETS_PER_USER} wallets"
        raise ValueError(error_msg)

    db_wallet = Wallet.model_validate(
        wallet_in,
        update={"user_id": user_id, "balance": Decimal("0.00")},
    )
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return db_wallet


def get_wallet_by_id(*, session: Session, wallet_id: uuid.UUID) -> Wallet | None:
    """Get wallet by ID."""
    return session.get(Wallet, wallet_id)


def get_user_wallets(*, session: Session, user_id: uuid.UUID) -> list[Wallet]:
    """Get all wallets for a user."""
    return list(session.exec(select(Wallet).where(Wallet.user_id == user_id)).all())


def get_user_wallet_by_currency(
    *,
    session: Session,
    user_id: uuid.UUID,
    currency: Currency,
) -> Wallet | None:
    """Get a user's wallet by currency."""
    return session.exec(
        select(Wallet).where(
            Wallet.user_id == user_id,
            Wallet.currency == currency,
        ),
    ).first()


# Transaction CRUD operations
def create_transaction(
    *,
    session: Session,
    transaction_in: TransactionCreate,
    user_id: uuid.UUID,
) -> Transaction:
    """Create a new transaction for a wallet."""
    # Get the wallet
    wallet = session.get(Wallet, transaction_in.wallet_id)
    if not wallet:
        error_msg = "Wallet not found"
        raise ValueError(error_msg)

    # Check if wallet belongs to user
    if wallet.user_id != user_id:
        error_msg = "Wallet does not belong to user"
        raise ValueError(error_msg)

    # Calculate new balance
    if transaction_in.type == TransactionType.CREDIT:
        new_balance = wallet.balance + transaction_in.amount
    else:  # DEBIT
        new_balance = wallet.balance - transaction_in.amount
        if new_balance < 0:
            error_msg = "Insufficient balance for debit transaction"
            raise ValueError(error_msg)

    # Create transaction
    db_transaction = Transaction.model_validate(
        transaction_in,
        update={"currency": wallet.currency},
    )
    session.add(db_transaction)

    # Update wallet balance
    wallet.balance = new_balance
    session.add(wallet)

    session.commit()
    session.refresh(db_transaction)
    return db_transaction


def get_wallet_transactions(
    *,
    session: Session,
    wallet_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100,
) -> list[Transaction]:
    """Get transactions for a wallet."""
    return list(
        session.exec(
            select(Transaction)
            .where(Transaction.wallet_id == wallet_id)
            .offset(skip)
            .limit(limit),
        ).all()
    )


def transfer_between_wallets(
    *,
    session: Session,
    transfer: WalletTransfer,
    user_id: uuid.UUID,
) -> tuple[Transaction, Transaction]:
    """Transfer money between two wallets with currency conversion if needed."""
    # Get both wallets
    from_wallet = session.get(Wallet, transfer.from_wallet_id)
    to_wallet = session.get(Wallet, transfer.to_wallet_id)

    if not from_wallet or not to_wallet:
        error_msg = "One or both wallets not found"
        raise ValueError(error_msg)

    # Check if both wallets belong to user
    if from_wallet.user_id != user_id or to_wallet.user_id != user_id:
        error_msg = "One or both wallets do not belong to user"
        raise ValueError(error_msg)

    # Check if from_wallet has sufficient balance
    if from_wallet.balance < transfer.amount:
        error_msg = "Insufficient balance in source wallet"
        raise ValueError(error_msg)

    # Convert currency if needed
    converted_amount, _fee = convert_with_fee(
        transfer.amount,
        from_wallet.currency,
        to_wallet.currency,
    )
    # Note: Fee is deducted from converted_amount in convert_with_fee function

    # Debit from source wallet
    from_wallet.balance -= transfer.amount
    debit_transaction = Transaction(
        wallet_id=from_wallet.id,
        amount=transfer.amount,
        type=TransactionType.DEBIT,
        currency=from_wallet.currency,
    )
    session.add(debit_transaction)

    # Credit to destination wallet (after conversion and fee)
    to_wallet.balance += converted_amount
    credit_transaction = Transaction(
        wallet_id=to_wallet.id,
        amount=converted_amount,
        type=TransactionType.CREDIT,
        currency=to_wallet.currency,
    )
    session.add(credit_transaction)

    # Update wallets
    session.add(from_wallet)
    session.add(to_wallet)

    session.commit()
    session.refresh(debit_transaction)
    session.refresh(credit_transaction)

    return debit_transaction, credit_transaction
