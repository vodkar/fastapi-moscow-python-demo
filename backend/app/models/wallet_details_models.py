"""Wallet details API model with transactions."""

import uuid
from datetime import datetime

from app.models.db_models import CurrencyType, TransactionType
from sqlmodel import SQLModel


class WalletWithTransactions(SQLModel):
    """Wallet model with transaction details."""

    id: uuid.UUID
    user_id: uuid.UUID
    balance: float
    currency: CurrencyType
    transactions: list["TransactionInWallet"]


class TransactionInWallet(SQLModel):
    """Transaction model for wallet details."""

    id: uuid.UUID
    amount: float
    transaction_type: TransactionType
    timestamp: datetime
    currency: CurrencyType
