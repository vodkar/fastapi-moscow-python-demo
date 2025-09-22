"""Wallet and Transaction API models."""

import uuid
from decimal import Decimal
from typing import Literal

from app.constants import STRING_MAX_LENGTH
from sqlmodel import Field, SQLModel

Currency = Literal["USD", "EUR", "RUB"]
TransactionType = Literal["credit", "debit"]


class WalletCreate(SQLModel):
    """Payload to create a wallet for the current user."""

    currency: Currency


class WalletPublic(SQLModel):
    """Public wallet representation."""

    id: uuid.UUID
    user_id: uuid.UUID
    currency: str = Field(min_length=3, max_length=STRING_MAX_LENGTH)
    balance: Decimal


class WalletsPublic(SQLModel):
    """List of wallets + count."""

    wallet_data: list[WalletPublic]
    count: int


class TransactionCreate(SQLModel):
    """Create a wallet transaction."""

    amount: Decimal
    type: TransactionType
    currency: Currency


class TransactionPublic(SQLModel):
    """Public transaction representation."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    type: TransactionType
    currency: Currency
