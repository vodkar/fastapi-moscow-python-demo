"""Wallet-related API models."""

import uuid

from app.models.db_models import Currency
from sqlmodel import SQLModel


class WalletBase(SQLModel):
    """Base wallet model."""

    currency: Currency


class WalletCreate(WalletBase):
    """Model for creating a wallet."""

    pass


class WalletPublic(WalletBase):
    """Public wallet model for API responses."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: float


class WalletsPublic(SQLModel):
    """Collection of public wallets."""

    wallet_data: list[WalletPublic]
    count: int
