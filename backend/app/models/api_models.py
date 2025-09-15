"""API response and utility models."""

import uuid

from pydantic import EmailStr
from sqlmodel import Field, SQLModel

from app.constants import (
    EMAIL_MAX_LENGTH,
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    STRING_MAX_LENGTH,
)

TOKEN_TYPE_BEARER = "bearer"  # noqa: S105


class UserPublic(SQLModel):
    """Public user model for API responses."""

    id: uuid.UUID
    email: EmailStr = Field(unique=True, index=True, max_length=EMAIL_MAX_LENGTH)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)


class UsersPublic(SQLModel):
    """Collection of public users."""

    user_data: list[UserPublic]
    count: int


class Message(SQLModel):
    """Generic message model."""

    message: str


class Token(SQLModel):
    """JWT token model."""

    access_token: str
    token_type: str = TOKEN_TYPE_BEARER


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
