"""Wallet and Transaction management endpoints."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from sqlmodel import func, select

from app.api.deps import CurrentUser, SessionDep
from app.constants import BAD_REQUEST_CODE, CONFLICT_CODE, NOT_FOUND_CODE
from typing import cast

from app.core.currency import Currency, apply_fee, convert, quantize_money
from app.models import (
    Transaction,
    TransactionCreate,
    TransactionPublic,
    Wallet,
    WalletCreate,
    WalletPublic,
)

router = APIRouter(prefix="/wallets", tags=["wallets"])


@router.post("/")
def create_wallet(
    *, session: SessionDep, current_user: CurrentUser, wallet_in: WalletCreate
) -> WalletPublic:
    """Create a wallet for the current user in the given currency.

    Rules:
    - Max 3 wallets per user
    - One wallet per currency
    - Balance starts at 0.00
    """
    count_stmt = (
        select(func.count())
        .select_from(Wallet)
        .where(Wallet.user_id == current_user.id)
    )
    current_count = session.exec(count_stmt).one()
    if current_count >= 3:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE, detail="User wallet limit reached"
        )

    existing_stmt = select(Wallet).where(
        Wallet.user_id == current_user.id, Wallet.currency == wallet_in.currency
    )
    if session.exec(existing_stmt).first():
        raise HTTPException(
            status_code=CONFLICT_CODE, detail="Wallet for this currency already exists"
        )

    db_wallet = Wallet(
        user_id=current_user.id,
        currency=wallet_in.currency,
        balance=Decimal("0.00"),
    )
    session.add(db_wallet)
    session.commit()
    session.refresh(db_wallet)
    return WalletPublic.model_validate(db_wallet)


@router.get("/{wallet_id}")
def read_wallet(
    *, session: SessionDep, current_user: CurrentUser, wallet_id: uuid.UUID
) -> WalletPublic:
    db_wallet = session.get(Wallet, wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE, detail="Not enough permissions"
        )
    return WalletPublic.model_validate(db_wallet)


@router.post("/{wallet_id}/transactions")
def create_transaction(
    *,
    session: SessionDep,
    current_user: CurrentUser,
    wallet_id: uuid.UUID,
    txn_in: TransactionCreate,
) -> TransactionPublic:
    """Create a credit/debit transaction on a wallet with currency conversion and fees.

    - Credit: add to balance
    - Debit: subtract from balance, cannot go negative
    - If txn currency != wallet currency: convert and apply fee (on converted amount)
    """
    db_wallet = session.get(Wallet, wallet_id)
    if not db_wallet:
        raise HTTPException(status_code=NOT_FOUND_CODE, detail="Wallet not found")
    if not current_user.is_superuser and db_wallet.user_id != current_user.id:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE, detail="Not enough permissions"
        )

    # Normalize amount to 2 decimals
    amount = quantize_money(Decimal(txn_in.amount))
    if amount <= 0:
        raise HTTPException(
            status_code=BAD_REQUEST_CODE, detail="Amount must be positive"
        )

    # Convert if currencies differ
    cross = txn_in.currency != db_wallet.currency
    effective_amount = (
        convert(
            amount, cast(Currency, txn_in.currency), cast(Currency, db_wallet.currency)
        )
        if cross
        else amount
    )
    effective_amount = apply_fee(effective_amount, cross_currency=cross)

    new_balance = Decimal(db_wallet.balance)
    if txn_in.type == "credit":
        new_balance = quantize_money(new_balance + effective_amount)
    else:  # debit
        if new_balance - effective_amount < Decimal("0.00"):
            raise HTTPException(
                status_code=BAD_REQUEST_CODE,
                detail="Insufficient funds",
            )
        new_balance = quantize_money(new_balance - effective_amount)

    # Persist transaction and update balance atomically
    db_txn = Transaction(
        wallet_id=db_wallet.id,
        amount=amount,  # store original amount in original currency for audit
        type=txn_in.type,
        currency=txn_in.currency,
    )
    db_wallet.balance = new_balance
    session.add(db_txn)
    session.add(db_wallet)
    session.commit()
    session.refresh(db_txn)
    return TransactionPublic.model_validate(db_txn)
