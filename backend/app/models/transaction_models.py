"""Transaction-related API models."""

import uuid
from datetime import datetime

from app.models.db_models import Currency, TransactionType
from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    """Base transaction model."""

    amount: float = Field(gt=0.0)
    type: TransactionType
    currency: Currency


class TransactionCreate(TransactionBase):
    """Model for creating a transaction."""

    wallet_id: uuid.UUID


class TransactionPublic(TransactionBase):
    """Public transaction model for API responses."""

    id: uuid.UUID
    wallet_id: uuid.UUID
    timestamp: datetime


class TransactionsPublic(SQLModel):
    """Collection of public transactions."""

    transaction_data: list[TransactionPublic]
    count: int
