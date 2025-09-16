"""Database table models."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.constants import EMAIL_MAX_LENGTH, STRING_MAX_LENGTH


class CurrencyEnum(StrEnum):
    """Available currencies for wallets."""

    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"


class TransactionTypeEnum(StrEnum):
    """Transaction types."""

    CREDIT = "credit"
    DEBIT = "debit"


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
        back_populates="owner", cascade_delete=True
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
    """Database wallet model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    currency: CurrencyEnum = Field(index=True)
    owner: User | None = Relationship(back_populates="wallet_list")
    transaction_list: list["Transaction"] = Relationship(
        back_populates="wallet", cascade_delete=True
    )


class Transaction(SQLModel, table=True):
    """Database transaction model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id",
        nullable=False,
        ondelete="CASCADE",
        index=True,
    )
    amount: Decimal = Field(decimal_places=2)
    transaction_type: TransactionTypeEnum = Field(alias="type")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), index=True
    )
    currency: CurrencyEnum
    wallet: Wallet | None = Relationship(back_populates="transaction_list")
