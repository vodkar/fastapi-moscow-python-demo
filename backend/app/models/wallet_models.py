"""Wallet and transaction API models."""

from __future__ import annotations

import uuid
from decimal import Decimal

from app.constants import Currency, TransactionType
from sqlmodel import Field, SQLModel


class WalletCreate(SQLModel):
    """Payload to create a new wallet for the current user.

    Attributes:
        currency: Desired wallet currency. Must be one of supported values.
    """

    currency: Currency = Field(nullable=False)


class WalletPublic(SQLModel):
    """Public wallet representation returned by the API."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    currency: Currency


class TransactionCreate(SQLModel):
    """Payload to create a transaction for a wallet.

    Attributes:
        amount: Positive decimal amount with two decimals.
        type: 'credit' or 'debit'.
        currency: Currency of the transaction funds (may differ from wallet).
    """

    amount: Decimal
    type: TransactionType
    currency: Currency


class TransactionPublic(SQLModel):
    """Public transaction representation returned by the API."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    type: TransactionType
    currency: Currency


class WalletWithTransactions(WalletPublic):
    """Wallet details including transactions list and count."""

    transactions: list[TransactionPublic] = []
    transaction_count: int = 0
