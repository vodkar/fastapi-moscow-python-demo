"""Wallet-related data models."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel

from app.models.db_models import CurrencyEnum, TransactionTypeEnum


class WalletBase(SQLModel):
    """Base wallet model with shared fields."""

    currency: CurrencyEnum


class WalletCreate(WalletBase):
    """Wallet creation model."""


class WalletPublic(WalletBase):
    """Public wallet model for API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal
    currency: CurrencyEnum


class WalletsPublic(SQLModel):
    """Public model for multiple wallets."""

    wallet_data: list[WalletPublic]
    count: int


class TransactionBase(SQLModel):
    """Base transaction model with shared fields."""

    amount: Decimal = Field(decimal_places=2, gt=0)
    transaction_type: TransactionTypeEnum = Field(alias="type")


class TransactionCreate(TransactionBase):
    """Transaction creation model."""

    wallet_id: uuid.UUID


class TransactionPublic(TransactionBase):
    """Public transaction model for API responses."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    amount: Decimal
    transaction_type: TransactionTypeEnum = Field(alias="type")
    timestamp: datetime
    currency: CurrencyEnum


class TransactionsPublic(SQLModel):
    """Public model for multiple transactions."""

    transaction_data: list[TransactionPublic]
    count: int


class WalletTransferCreate(SQLModel):
    """Model for wallet-to-wallet transfers."""

    from_wallet_id: uuid.UUID
    to_wallet_id: uuid.UUID
    amount: Decimal = Field(decimal_places=2, gt=0)
