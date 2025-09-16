"""Wallet management API endpoints."""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal

from app.api.deps import CurrentUser, SessionDep
from app.constants import (
    BAD_REQUEST_CODE,
    CONFLICT_CODE,
    CROSS_CURRENCY_FEE_RATE,
    DECIMAL_QUANT,
    EXCHANGE_RATES,
    MAX_WALLETS_PER_USER,
    NOT_FOUND_CODE,
    Currency,
    TransactionType,
)
from app.models import (
    Transaction,
    TransactionCreate,
    TransactionPublic,
    Wallet,
    WalletCreate,
    WalletPublic,
)
from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

router = APIRouter(prefix="/wallets", tags=["wallets"])


def _quantize(amount: Decimal) -> Decimal:
    """Quantize a decimal amount to two decimal places with HALF_UP rounding."""

    return amount.quantize(DECIMAL_QUANT, rounding=ROUND_HALF_UP)


def _convert_amount(
    amount: Decimal,
    from_currency: Currency,
    to_currency: Currency,
) -> tuple[Decimal, bool]:
    """Convert amount between currencies using fixed rates.

    Args:
        amount: Original amount in from_currency.
        from_currency: Source currency.
        to_currency: Target currency (wallet currency).

    Returns:
        Tuple of (converted_amount_in_target_currency, is_cross_currency)
    """

    if from_currency == to_currency:
        return (_quantize(amount), False)
    rate = EXCHANGE_RATES.get((from_currency, to_currency))
    if rate is None:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Unsupported currency conversion",
        )
    converted = _quantize(amount * rate)
    return (converted, True)


@router.post("/")
def create_wallet(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_in: WalletCreate,
) -> WalletPublic:
    """Create a new wallet for the current user.

    Enforces a maximum of three wallets per user and initializes balance to 0.00.
    """

    # Enforce wallet limit per user
    count_statement = (
        select(func.count())
        .select_from(Wallet)
        .where(Wallet.user_id == current_user.id)
    )
    user_wallet_count = session.exec(count_statement).one()
    if user_wallet_count >= MAX_WALLETS_PER_USER:
        raise HTTPException(
            status_code=CONFLICT_CODE,
            detail="User has reached the maximum number of wallets",
        )

    db_wallet = Wallet(
        user_id=current_user.id,
        balance=Decimal("0.00"),
        currency=wallet_in.currency,
    )
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return WalletPublic.model_validate(db_wallet)


def _ensure_wallet_access(wallet: Wallet | None, current_user: CurrentUser) -> Wallet:
    if not wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Not enough permissions",
        )
    return wallet


@router.get("/{wallet_id}")
def read_wallet(
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
) -> WalletPublic:
    """Retrieve wallet details, including current balance."""

    db_wallet = session.get(Wallet, wallet_id)
    _ensure_wallet_access(db_wallet, current_user)
    return WalletPublic.model_validate(db_wallet)


@router.post("/{wallet_id}/transactions")
def create_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    tx_in: TransactionCreate,
) -> TransactionPublic:
    """Create a credit or debit transaction for a wallet.

    - Credits add to the wallet balance.
    - Debits subtract from the wallet balance (cannot go negative).
    - Cross-currency transactions are converted and charged a fee.
    """

    if tx_in.amount <= Decimal("0"):
        raise HTTPException(
            status_code=BAD_REQUEST_CODE,
            detail="Amount must be greater than zero",
        )

    db_wallet = session.get(Wallet, wallet_id)
    wallet = _ensure_wallet_access(db_wallet, current_user)

    # Convert amount to wallet currency if needed
    converted_amount, is_cross = _convert_amount(
        amount=tx_in.amount,
        from_currency=tx_in.currency,
        to_currency=wallet.currency,
    )

    # Apply cross-currency fee on the converted amount
    if is_cross and CROSS_CURRENCY_FEE_RATE > 0:
        fee_amount = _quantize(converted_amount * CROSS_CURRENCY_FEE_RATE)
        net_amount = _quantize(converted_amount - fee_amount)
    else:
        net_amount = converted_amount

    # Adjust balance based on transaction type
    if tx_in.type == TransactionType.CREDIT:
        new_balance = _quantize(wallet.balance + net_amount)
    else:  # DEBIT
        new_balance = _quantize(wallet.balance - net_amount)
        if new_balance < Decimal("0"):
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail="Insufficient funds for debit transaction",
            )

    wallet.balance = new_balance
    session.add(wallet)

    db_tx = Transaction(
        wallet_id=wallet.id,
        amount=_quantize(tx_in.amount),  # store original amount
        type=tx_in.type,
        currency=tx_in.currency,
    )
    session.add(db_tx)
    session.commit()
    session.refresh(db_tx)
    return TransactionPublic.model_validate(db_tx)
