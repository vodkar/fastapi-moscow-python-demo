"""Item-related data models."""

import uuid

from sqlmodel import Field, SQLModel

from app.constants import STRING_MAX_LENGTH


class ItemBase(SQLModel):
    """Base item model with shared fields."""

    title: str = Field(min_length=1, max_length=STRING_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=STRING_MAX_LENGTH)


class ItemCreate(ItemBase):
    """Item creation model."""


class ItemUpdate(ItemBase):
    """Item update model."""

    title: str | None = Field(default=None, min_length=1, max_length=STRING_MAX_LENGTH)  # type: ignore[assignment]


class ItemPublic(ItemBase):
    """Public item model for API responses."""

    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    """Collection of public items."""

    item_data: list[ItemPublic]
    count: int
