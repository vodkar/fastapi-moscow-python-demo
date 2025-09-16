"""Wallet-related data models."""

import uuid

from app.models.db_models import CurrencyType
from sqlmodel import SQLModel


class WalletBase(SQLModel):
    """Base wallet model with shared fields."""

    currency: CurrencyType


class WalletCreate(WalletBase):
    """Wallet creation model."""


class WalletPublic(WalletBase):
    """Public wallet model for API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: float


class WalletsPublic(SQLModel):
    """Collection of public wallets."""

    wallet_data: list[WalletPublic]
    count: int
