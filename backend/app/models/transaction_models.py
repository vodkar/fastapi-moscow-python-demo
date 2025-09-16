"""Transaction-related data models."""

import uuid
from datetime import datetime

from app.models.db_models import CurrencyType, TransactionType
from sqlmodel import Field, SQLModel


class TransactionBase(SQLModel):
    """Base transaction model with shared fields."""

    amount: float = Field(gt=0.0)
    transaction_type: TransactionType
    currency: CurrencyType


class TransactionCreate(TransactionBase):
    """Transaction creation model."""

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
