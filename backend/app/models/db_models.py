"""Database table models."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel

from app.constants import EMAIL_MAX_LENGTH, STRING_MAX_LENGTH


class Currency(str, Enum):
    """Supported currencies."""

    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"


class TransactionType(str, Enum):
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
    wallets: list["Wallet"] = Relationship(back_populates="user", cascade_delete=True)


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
    )
    balance: Decimal = Field(default=Decimal("0.00"), decimal_places=2)
    currency: Currency = Field(index=True)
    user: User | None = Relationship(back_populates="wallets")
    transactions: list["Transaction"] = Relationship(
        back_populates="wallet", cascade_delete=True
    )


class Transaction(SQLModel, table=True):
    """Database transaction model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id",
        nullable=False,
        ondelete="CASCADE",
    )
    amount: Decimal = Field(decimal_places=2)
    type: TransactionType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    currency: Currency
    wallet: Wallet | None = Relationship(back_populates="transactions")
