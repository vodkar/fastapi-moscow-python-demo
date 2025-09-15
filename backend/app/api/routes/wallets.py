"""Wallet management API endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, NOT_FOUND_CODE
from app.models import (
    Currency,
    Transaction,
    TransactionCreate,
    TransactionPublic,
    TransactionType,
    Wallet,
    WalletCreate,
    WalletPublic,
    WalletsPublic,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])

# Constants
MAX_WALLETS_PER_USER = 3

# Exchange rates (hardcoded for simplicity)
EXCHANGE_RATES = {
    ("USD", "EUR"): Decimal("0.85"),
    ("USD", "RUB"): Decimal("75.00"),
    ("EUR", "USD"): Decimal("1.18"),
    ("EUR", "RUB"): Decimal("88.24"),
    ("RUB", "USD"): Decimal("0.013"),
    ("RUB", "EUR"): Decimal("0.011"),
}

# Transaction fees (2% for currency conversion)
CONVERSION_FEE_RATE = Decimal("0.02")


@router.post("/", status_code=201)
def create_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create new wallet for user."""
    # Check if user already has 3 wallets
    count_statement = (
        select(func.count())
        .select_from(Wallet)
        .where(Wallet.user_id == current_user.id)
    )
    wallet_count = session.exec(count_statement).one()

    if wallet_count >= MAX_WALLETS_PER_USER:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=f"User can have maximum {MAX_WALLETS_PER_USER} wallets",
        )

    # Check if user already has wallet with this currency
    existing_wallet = session.exec(
        select(Wallet).where(
            Wallet.user_id == current_user.id, Wallet.currency == wallet_in.currency
        )
    ).first()

    if existing_wallet:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail=f"User already has a wallet with currency {wallet_in.currency}",
        )

    # Create wallet
    wallet = Wallet(
        user_id=current_user.id, currency=wallet_in.currency, balance=Decimal("0.00")
    )
    session.add(wallet)
    session.commit()
    session.refresh(wallet)

    return WalletPublic(
        id=str(wallet.id),
        user_id=str(wallet.user_id),
        balance=wallet.balance,
        currency=wallet.currency.value,
    )


@router.get("/")
def get_user_wallets(
    session: SessionDep,
    current_user: CurrentUser,
) -> WalletsPublic:
    """Get all wallets for current user."""
    statement = select(Wallet).where(Wallet.user_id == current_user.id)
    wallets = session.exec(statement).all()

    wallet_list = [
        WalletPublic(
            id=str(wallet.id),
            user_id=str(wallet.user_id),
            balance=wallet.balance,
            currency=wallet.currency.value,
        )
        for wallet in wallets
    ]

    return WalletsPublic(data=wallet_list, count=len(wallet_list))


@router.get("/{wallet_id}")
def get_wallet_details(
    wallet_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
) -> WalletPublic:
    """Get wallet details including current balance."""
    wallet = session.get(Wallet, wallet_id)

    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if wallet.user_id != current_user.id:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    return WalletPublic(
        id=str(wallet.id),
        user_id=str(wallet.user_id),
        balance=wallet.balance,
        currency=wallet.currency.value,
    )


@router.post("/{wallet_id}/transactions", status_code=201)
def create_transaction(
    wallet_id: uuid.UUID,
    *,
    session: SessionDep,
    current_user: CurrentUser,
    transaction_in: TransactionCreate,
) -> TransactionPublic:
    """Create a transaction (credit or debit) for a wallet."""
    # Get wallet
    wallet = session.get(Wallet, wallet_id)

    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if wallet.user_id != current_user.id:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    # Calculate the effective amount after currency conversion and fees
    effective_amount = transaction_in.amount
    conversion_fee = Decimal("0.00")

    # Handle currency conversion
    if transaction_in.currency != wallet.currency.value:
        # Convert amount to wallet currency
        rate_key = (transaction_in.currency, wallet.currency.value)
        if rate_key not in EXCHANGE_RATES:
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail=(
                    f"Currency conversion from {transaction_in.currency} to "
                    f"{wallet.currency.value} not supported"
                ),
            )

        conversion_rate = EXCHANGE_RATES[rate_key]
        effective_amount = transaction_in.amount * conversion_rate
        conversion_fee = effective_amount * CONVERSION_FEE_RATE
        effective_amount -= conversion_fee

    # Check balance for debit transactions
    if transaction_in.type == TransactionType.DEBIT.value:
        if wallet.balance < effective_amount:
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail="Insufficient balance for debit transaction",
            )
        # Update wallet balance
        wallet.balance -= effective_amount
    else:  # Credit transaction
        wallet.balance += effective_amount

    # Round to 2 decimal places
    wallet.balance = wallet.balance.quantize(Decimal("0.01"))

    # Create transaction
    transaction = Transaction(
        wallet_id=wallet_id,
        amount=transaction_in.amount,
        type=TransactionType(transaction_in.type),
        currency=Currency(transaction_in.currency),
    )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return TransactionPublic(
        id=str(transaction.id),
        wallet_id=str(transaction.wallet_id),
        amount=transaction.amount,
        type=transaction.type.value,
        currency=transaction.currency.value,
        timestamp=transaction.timestamp,
    )


@router.get("/{wallet_id}/transactions")
def get_wallet_transactions(
    wallet_id: uuid.UUID,
    session: SessionDep,
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
) -> list[TransactionPublic]:
    """Get transactions for a wallet."""
    # Check wallet ownership
    wallet = session.get(Wallet, wallet_id)

    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    if wallet.user_id != current_user.id:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")

    # Get transactions
    statement = (
        select(Transaction)
        .where(Transaction.wallet_id == wallet_id)
        .order_by(Transaction.timestamp.desc())
        .offset(skip)
        .limit(limit)
    )
    transactions = session.exec(statement).all()

    return [
        TransactionPublic(
            id=str(transaction.id),
            wallet_id=str(transaction.wallet_id),
            amount=transaction.amount,
            type=transaction.type.value,
            currency=transaction.currency.value,
            timestamp=transaction.timestamp,
        )
        for transaction in transactions
    ]
