"""CRUD operations for database models."""

import uuid
from decimal import Decimal

from sqlmodel import Session, select

from app.core.security import get_password_hash, verify_password
from app.models import (
    CurrencyEnum,
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


# Exchange rates (hardcoded as per requirements)
EXCHANGE_RATES: dict[tuple[CurrencyEnum, CurrencyEnum], Decimal] = {
    (CurrencyEnum.USD, CurrencyEnum.EUR): Decimal("0.85"),
    (CurrencyEnum.EUR, CurrencyEnum.USD): Decimal("1.18"),
    (CurrencyEnum.USD, CurrencyEnum.RUB): Decimal("90.00"),
    (CurrencyEnum.RUB, CurrencyEnum.USD): Decimal("0.011"),
    (CurrencyEnum.EUR, CurrencyEnum.RUB): Decimal("105.00"),
    (CurrencyEnum.RUB, CurrencyEnum.EUR): Decimal("0.0095"),
}

CONVERSION_FEE_RATE = Decimal("0.02")  # 2% fee for currency conversion


def create_wallet(
    *, session: Session, wallet_in: WalletCreate, user_id: uuid.UUID
) -> Wallet:
    """Create a new wallet for a user."""
    # Check if user already has 3 wallets
    statement = select(Wallet).where(Wallet.user_id == user_id)
    existing_wallets = session.exec(statement).all()

    if len(existing_wallets) >= 3:
        raise ValueError("User can only have a maximum of 3 wallets")

    # Check if user already has a wallet with this currency
    for wallet in existing_wallets:
        if wallet.currency == wallet_in.currency:
            raise ValueError(f"User already has a {wallet_in.currency} wallet")

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
    *,
    session: Session,
    transaction_in: TransactionCreate,
    target_wallet_id: uuid.UUID | None = None,
) -> Transaction:
    """Create a new transaction and update wallet balance."""
    # Get the source wallet
    source_wallet = session.get(Wallet, transaction_in.wallet_id)
    if not source_wallet:
        raise ValueError("Wallet not found")

    amount = transaction_in.amount
    transaction_currency = source_wallet.currency

    # Handle currency conversion if target wallet is specified
    if target_wallet_id:
        target_wallet = session.get(Wallet, target_wallet_id)
        if not target_wallet:
            raise ValueError("Target wallet not found")

        if source_wallet.currency != target_wallet.currency:
            # Convert currency and apply fee
            conversion_key = (source_wallet.currency, target_wallet.currency)
            if conversion_key not in EXCHANGE_RATES:
                raise ValueError(
                    f"Conversion not supported between {source_wallet.currency} and {target_wallet.currency}"
                )

            exchange_rate = EXCHANGE_RATES[conversion_key]
            converted_amount = amount * exchange_rate
            fee = converted_amount * CONVERSION_FEE_RATE
            final_amount = converted_amount - fee

            transaction_currency = target_wallet.currency
            amount = final_amount

    # Validate transaction based on type
    if transaction_in.transaction_type == TransactionTypeEnum.DEBIT:
        if source_wallet.balance < transaction_in.amount:
            raise ValueError("Insufficient balance for debit transaction")

        # Update source wallet balance (subtract)
        source_wallet.balance -= transaction_in.amount

        # If target wallet, add converted amount
        if target_wallet_id:
            target_wallet = session.get(Wallet, target_wallet_id)
            if target_wallet:
                target_wallet.balance += amount
                session.add(target_wallet)

    elif transaction_in.transaction_type == TransactionTypeEnum.CREDIT:
        # Update source wallet balance (add)
        source_wallet.balance += transaction_in.amount

    # Round balance to 2 decimal places
    source_wallet.balance = source_wallet.balance.quantize(Decimal("0.01"))

    # Create transaction record
    db_transaction = Transaction.model_validate(
        transaction_in,
        update={"currency": transaction_currency},
    )

    session.add(source_wallet)
    session.add(db_transaction)
    session.commit()
    session.refresh(db_transaction)

    return db_transaction


def get_wallet_transactions(
    *, session: Session, wallet_id: uuid.UUID
) -> list[Transaction]:
    """Get all transactions for a wallet."""
    statement = select(Transaction).where(Transaction.wallet_id == wallet_id)
    return list(session.exec(statement).all())
