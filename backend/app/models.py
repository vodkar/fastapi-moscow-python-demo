"""Data models for the application."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum

from pydantic import EmailStr, field_validator
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


# ---- Wallet & Transaction domain ----

ALLOWED_CURRENCIES = {"USD", "EUR", "RUB"}


class TransactionType(str, Enum):
    """Enumeration of transaction directions."""

    credit = "credit"
    debit = "debit"


class WalletBase(SQLModel):
    """Shared wallet fields."""

    currency: str = Field(description="Wallet currency (USD, EUR, RUB)")

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is one of supported list."""
        if v not in ALLOWED_CURRENCIES:
            msg = "Unsupported currency"
            raise ValueError(msg)
        return v


class WalletCreate(WalletBase):
    """Payload to create a wallet."""


class Wallet(WalletBase, table=True):
    """Wallet DB model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(
        foreign_key="user.id",
        nullable=False,
        ondelete="CASCADE",
    )
    # store balance as Decimal with 2 digits scale
    balance: Decimal = Field(
        default=Decimal("0.00"),
        description="Current balance",
    )
    transaction_list: list["Transaction"] = Relationship(
        back_populates="wallet",
        cascade_delete=True,
    )


class WalletPublic(WalletBase):
    """Wallet details sent to clients."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: Decimal


class WalletsPublic(SQLModel):
    """Collection of wallets."""

    wallet_data: list[WalletPublic]
    count: int


class TransactionBase(SQLModel):
    """Shared transaction fields."""

    amount: Decimal = Field(gt=0)  # type: ignore[arg-type]
    type: TransactionType
    currency: str

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency is one of supported list."""
        if v not in ALLOWED_CURRENCIES:
            msg = "Unsupported currency"
            raise ValueError(msg)
        return v


class TransactionCreate(TransactionBase):
    """Payload to create a transaction."""

    wallet_id: uuid.UUID
    # Optional target wallet for future extension; not used now.
    target_wallet_id: uuid.UUID | None = None


class Transaction(TransactionBase, table=True):
    """Transaction DB model."""

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    wallet_id: uuid.UUID = Field(
        foreign_key="wallet.id",
        nullable=False,
        ondelete="CASCADE",
    )
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    wallet: Wallet | None = Relationship(back_populates="transaction_list")


class TransactionPublic(TransactionBase):
    """Transaction details."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    timestamp: datetime


class TransactionsPublic(SQLModel):
    """Collection of transactions."""

    transaction_data: list[TransactionPublic]
    count: int
