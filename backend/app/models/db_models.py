"""Database table models."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from app.constants import EMAIL_MAX_LENGTH, STRING_MAX_LENGTH
from pydantic import EmailStr
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.types import Enum as SAEnum
from sqlalchemy.types import Numeric
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Database user model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=EMAIL_MAX_LENGTH)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)
    hashed_password: str
    item_list: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    wallet_list: list["Wallet"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )


class Item(SQLModel, table=True):
    """Database item model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(min_length=1, max_length=STRING_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    owner: User | None = Relationship(back_populates="item_list")


class Wallet(SQLModel, table=True):
    """Wallet model bound to a user and specific currency."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    currency: str = Field(min_length=3, max_length=STRING_MAX_LENGTH)
    # Use Decimal with fixed precision 2 for safe money math
    balance: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(18, 2), nullable=False, server_default="0.00"),
    )

    owner: User | None = Relationship(back_populates="wallet_list")
    transaction_list: list["Transaction"] = Relationship(
        back_populates="wallet",
        cascade_delete=True,
    )

    __table_args__ = (
        UniqueConstraint("user_id", "currency", name="uq_wallet_user_currency"),
    )


class Transaction(SQLModel, table=True):
    """Transaction for a wallet (credit or debit)."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id", nullable=False, ondelete="CASCADE"
    )
    amount: Decimal = Field(sa_column=Column(Numeric(18, 2), nullable=False))
    type: str = Field(
        sa_column=Column(
            SAEnum("credit", "debit", name="transaction_type"), nullable=False
        )
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    currency: str = Field(min_length=3, max_length=STRING_MAX_LENGTH)

    wallet: Wallet | None = Relationship(back_populates="transaction_list")
