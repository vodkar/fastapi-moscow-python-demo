"""Wallet-related data models."""

from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel


class WalletBase(SQLModel):
    """Base wallet model with shared fields."""

    currency: str


class WalletCreate(WalletBase):
    """Wallet creation model."""


class WalletPublic(WalletBase):
    """Public wallet model."""

    id: str
    user_id: str
    balance: Decimal
    currency: str


class TransactionBase(SQLModel):
    """Base transaction model with shared fields."""

    amount: Decimal = Field(decimal_places=2, ge=0)
    type: str
    currency: str


class TransactionCreate(TransactionBase):
    """Transaction creation model."""

    wallet_id: str


class TransactionPublic(TransactionBase):
    """Public transaction model."""

    id: str
    wallet_id: str
    timestamp: datetime


class WalletsPublic(SQLModel):
    """Public wallets collection model."""

    data: list[WalletPublic]
    count: int


class TransactionsPublic(SQLModel):
    """Public transactions collection model."""

    data: list[TransactionPublic]
    count: int
