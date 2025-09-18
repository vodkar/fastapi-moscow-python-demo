"""Database table models."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from app.constants import EMAIL_MAX_LENGTH, STRING_MAX_LENGTH, Currency, TransactionType
from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class User(SQLModel, table=True):
    """Database user model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email: EmailStr = Field(unique=True, index=True, max_length=EMAIL_MAX_LENGTH)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)
    hashed_password: str
    item_list: list["Item"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )
    wallet_list: list["Wallet"] = Relationship(
        back_populates="user",
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
    """Wallet table linked to a user and holding a currency balance.

    Balance uses Decimal for precision and is stored with two decimal places.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    balance: Decimal = Field(default=Decimal("0.00"), nullable=False)
    currency: Currency = Field(nullable=False)

    user: User | None = Relationship(back_populates="wallet_list")
    transaction_list: list["Transaction"] = Relationship(
        back_populates="wallet",
        cascade_delete=True,
    )


class Transaction(SQLModel, table=True):
    """Transaction table for credits and debits on a wallet.

    Currency is recorded for the transaction; when cross-currency, conversion is applied.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id",
        nullable=False,
        index=True,
        ondelete="CASCADE",
    )
    amount: Decimal = Field(nullable=False)
    type: TransactionType = Field(nullable=False)
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
    )
    currency: Currency = Field(nullable=False)

    wallet: Wallet | None = Relationship(back_populates="transaction_list")
