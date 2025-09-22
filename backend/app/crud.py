"""CRUD operations for database models."""

import uuid
from decimal import Decimal

from sqlmodel import Session, desc, select

from app.constants import MAX_WALLETS_PER_USER
from app.core.security import get_password_hash, verify_password
from app.currency_service import convert_with_fee
from app.models import (
    Item,
    ItemCreate,
    Transaction,
    TransactionCreate,
    TransactionTypeEnum,
    User,
    UserCreate,
    UserUpdate,
    Wallet,
    WalletCreate,
    WalletTransferCreate,
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


def create_wallet(
    *, session: Session, wallet_in: WalletCreate, user_id: uuid.UUID
) -> Wallet:
    """Create a new wallet for a user."""
    # Check if user already has 3 wallets
    existing_wallets = session.exec(
        select(Wallet).where(Wallet.user_id == user_id)
    ).all()

    if len(existing_wallets) >= MAX_WALLETS_PER_USER:
        error_message = (
            f"User already has maximum number of wallets ({MAX_WALLETS_PER_USER})"
        )
        raise ValueError(error_message)

    # Check if user already has a wallet with this currency
    existing_currency_wallet = session.exec(
        select(Wallet).where(
            Wallet.user_id == user_id, Wallet.currency == wallet_in.currency
        )
    ).first()

    if existing_currency_wallet:
        error_message = f"User already has a wallet with currency {wallet_in.currency}"
        raise ValueError(error_message)

    db_wallet = Wallet.model_validate(
        wallet_in, update={"user_id": user_id, "balance": Decimal("0.00")}
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
    statement = select(Wallet).where(Wallet.user_id == user_id)
    return list(session.exec(statement).all())


def create_transaction(
    *, session: Session, transaction_in: TransactionCreate, wallet: Wallet
) -> Transaction:
    """Create a new transaction and update wallet balance."""
    if transaction_in.transaction_type == TransactionTypeEnum.DEBIT:
        new_balance = wallet.balance - transaction_in.amount
        if new_balance < 0:
            error_message = (
                "Insufficient funds: transaction would result in negative balance"
            )
            raise ValueError(error_message)
        wallet.balance = new_balance
    else:  # CREDIT
        wallet.balance += transaction_in.amount

    db_transaction = Transaction.model_validate(
        transaction_in, update={"currency": wallet.currency}
    )
    session.add(db_transaction)
    session.add(wallet)
    session.commit()
    session.refresh(db_transaction)
    session.refresh(wallet)
    return db_transaction


def get_wallet_transactions(
    *, session: Session, wallet_id: uuid.UUID, skip: int = 0, limit: int = 100
) -> list[Transaction]:
    """Get transactions for a wallet."""
    statement = (
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(desc(Transaction.timestamp))
        .offset(skip)
        .limit(limit)
    )
    return list(session.exec(statement).all())


def transfer_between_wallets(
    *,
    session: Session,
    transfer_in: WalletTransferCreate,
    user_id: uuid.UUID,
) -> tuple[Transaction, Transaction]:
    """Transfer funds between user's wallets with currency conversion if needed."""
    # Get both wallets and validate ownership
    from_wallet = session.get(Wallet, transfer_in.from_wallet_id)
    to_wallet = session.get(Wallet, transfer_in.to_wallet_id)

    if not from_wallet or not to_wallet:
        error_message = "One or both wallets not found"
        raise ValueError(error_message)

    if from_wallet.user_id != user_id or to_wallet.user_id != user_id:
        error_message = "Both wallets must belong to the requesting user"
        raise ValueError(error_message)

    if from_wallet.id == to_wallet.id:
        error_message = "Cannot transfer to the same wallet"
        raise ValueError(error_message)

    # Check if source wallet has sufficient funds
    if from_wallet.balance < transfer_in.amount:
        error_message = "Insufficient funds in source wallet"
        raise ValueError(error_message)

    # Calculate conversion and fees
    converted_amount, _conversion_fee = convert_with_fee(
        transfer_in.amount,
        from_wallet.currency,
        to_wallet.currency,
    )

    # Update wallet balances
    from_wallet.balance -= transfer_in.amount
    to_wallet.balance += converted_amount

    # Create debit transaction for source wallet
    debit_transaction = Transaction(
        wallet_id=from_wallet.id,
        amount=transfer_in.amount,
        transaction_type=TransactionTypeEnum.DEBIT,
        currency=from_wallet.currency,
    )

    # Create credit transaction for destination wallet
    credit_transaction = Transaction(
        wallet_id=to_wallet.id,
        amount=converted_amount,
        transaction_type=TransactionTypeEnum.CREDIT,
        currency=to_wallet.currency,
    )

    # Add all changes to session
    session.add(from_wallet)
    session.add(to_wallet)
    session.add(debit_transaction)
    session.add(credit_transaction)

    session.commit()

    # Refresh objects
    session.refresh(from_wallet)
    session.refresh(to_wallet)
    session.refresh(debit_transaction)
    session.refresh(credit_transaction)

    return debit_transaction, credit_transaction
