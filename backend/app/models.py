"""Data models for the application.

Includes user, item plus wallet & transaction domain models.
"""

import uuid
from datetime import UTC, datetime
from decimal import ROUND_DOWN, Decimal, getcontext
from enum import Enum

from pydantic import EmailStr, field_validator
from sqlalchemy import Column, Numeric
from sqlmodel import Field, Relationship, SQLModel

from app.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    STRING_MAX_LENGTH,
)

# Token type constant to avoid hardcoded string
TOKEN_TYPE_BEARER = "bearer"  # noqa: S105


# Shared properties
class UserBase(SQLModel):
    """Base user model with shared fields."""

    email: EmailStr = Field(unique=True, index=True, max_length=EMAIL_MAX_LENGTH)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)


# Properties to receive via API on creation
class UserCreate(UserBase):
    """User creation model."""

    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )


class UserRegister(SQLModel):
    """User registration model."""

    email: EmailStr = Field(max_length=EMAIL_MAX_LENGTH)
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    """User update model."""

    email: EmailStr | None = Field(default=None, max_length=STRING_MAX_LENGTH)  # type: ignore[assignment]
    password: str | None = Field(
        default=None,
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )


class UserUpdateMe(SQLModel):
    """User self-update model."""

    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)
    email: EmailStr | None = Field(default=None, max_length=STRING_MAX_LENGTH)


class UpdatePassword(SQLModel):
    """Password update model."""

    current_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
    new_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )


# Database model, database table inferred from class name
class User(UserBase, table=True):
    """Database user model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    item_list: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)
    wallet_list: list["Wallet"] = Relationship(
        back_populates="owner",
        cascade_delete=True,
    )


# Properties to return via API, id is always required
class UserPublic(UserBase):
    """Public user model for API responses."""

    id: uuid.UUID


class UsersPublic(SQLModel):
    """Collection of public users."""

    user_data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    """Base item model with shared fields."""

    title: str = Field(min_length=1, max_length=STRING_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    """Item creation model."""


# Properties to receive on item update
class ItemUpdate(ItemBase):
    """Item update model."""

    title: str | None = Field(default=None, min_length=1, max_length=STRING_MAX_LENGTH)  # type: ignore[assignment]


# Database model, database table inferred from class name
class Item(ItemBase, table=True):  # noqa: WPS110
    """Database item model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    owner: User | None = Relationship(back_populates="item_list")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    """Public item model for API responses."""

    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    """Collection of public items."""

    item_data: list[ItemPublic]
    count: int


# ================= Wallet & Transaction Domain ==================

AVAILABLE_CURRENCIES = {"USD", "EUR", "RUB"}


class TransactionType(str, Enum):
    """Enumeration for transaction types."""

    CREDIT = "credit"
    DEBIT = "debit"


DECIMAL_PLACES = Decimal("0.01")
getcontext().prec = 28  # high precision, quantize later


def _quantize(value: Decimal) -> Decimal:
    """Quantize decimal to two places using ROUND_DOWN for consistency.

    Args:
        value: Raw decimal value.

    Returns:
        Decimal: Quantized value with 2 decimal places.

    """
    return value.quantize(DECIMAL_PLACES, rounding=ROUND_DOWN)


class WalletBase(SQLModel):
    """Base wallet shared properties."""

    currency: str = Field(description="Currency code (USD, EUR, RUB)")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        """Validate currency code membership."""
        if value not in AVAILABLE_CURRENCIES:
            msg = "Unsupported currency"
            raise ValueError(msg)
        return value


class Wallet(WalletBase, table=True):  # type: ignore[too-many-ancestors]
    """Wallet database model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    balance: Decimal = Field(
        default=Decimal("0.00"),
        description="Wallet balance in smallest precision (2 decimals)",
        sa_column=Column(Numeric(12, 2), default=Decimal("0.00")),
    )
    owner: User | None = Relationship(back_populates="wallet_list")
    transaction_list: list["Transaction"] = Relationship(
        back_populates="wallet",
        cascade_delete=True,
    )

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value: Decimal) -> Decimal:
        """Ensure balance always stored with 2 decimal places."""
        return _quantize(value)


class WalletCreate(WalletBase):
    """Wallet creation payload."""


class WalletPublic(WalletBase):
    """Wallet public representation."""

    id: uuid.UUID
    owner_id: uuid.UUID
    balance: Decimal

    @field_validator("balance")
    @classmethod
    def validate_balance(cls, value: Decimal) -> Decimal:
        """Ensure balance always serializes with 2 decimals."""
        return _quantize(value)


class WalletsPublic(SQLModel):
    """Collection of wallets."""

    wallet_data: list[WalletPublic]
    count: int


class TransactionBase(SQLModel):
    """Base transaction shared properties."""

    amount: Decimal = Field(
        description="Amount in transaction currency, positive",
        sa_column=Column(Numeric(12, 2)),
    )
    type: TransactionType
    currency: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        """Validate currency code membership."""
        if value not in AVAILABLE_CURRENCIES:
            msg = "Unsupported currency"
            raise ValueError(msg)
        return value

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value: Decimal) -> Decimal:
        """Validate amount positive and quantize."""
        if value <= 0:
            msg = "Amount must be greater than zero"
            raise ValueError(msg)
        return _quantize(value)


class Transaction(TransactionBase, table=True):  # type: ignore[too-many-ancestors]
    """Transaction database model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id",
        nullable=False,
        ondelete="CASCADE",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    wallet: Wallet | None = Relationship(back_populates="transaction_list")


class TransactionCreate(TransactionBase):
    """Transaction creation payload."""


class TransactionPublic(TransactionBase):
    """Transaction public schema."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    timestamp: datetime


# Generic message
class Message(SQLModel):
    """Generic message model."""

    message: str


# JSON payload containing access token
class Token(SQLModel):
    """JWT token model."""

    access_token: str
    token_type: str = TOKEN_TYPE_BEARER


# Contents of JWT token
class TokenPayload(SQLModel):
    """JWT token payload model."""

    sub: str | None = None


class NewPassword(SQLModel):
    """New password model."""

    token: str
    new_password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
    )
