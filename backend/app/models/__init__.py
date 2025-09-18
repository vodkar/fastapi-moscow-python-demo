"""Data models for the application."""

# API models
# Database models
from app.models.api_models import (
    Message,
    NewPassword,
    Token,
    TokenPayload,
    UserPublic,
    UsersPublic,
)
from app.models.db_models import Item, Transaction, User, Wallet

# Item models
from app.models.item_models import (
    ItemBase,
    ItemCreate,
    ItemPublic,
    ItemsPublic,
    ItemUpdate,
)

# User models
from app.models.user_models import (
    UpdatePassword,
    UserBase,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserUpdateMe,
)

# Wallet models
from app.models.wallet_models import (
    TransactionCreate,
    TransactionPublic,
    WalletCreate,
    WalletPublic,
    WalletWithTransactions,
)

__all__ = [
    # API models
    "Message",
    "NewPassword",
    "Token",
    "TokenPayload",
    "UserPublic",
    "UsersPublic",
    # Database models
    "Item",
    "Wallet",
    "Transaction",
    "User",
    # Item models
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
    # User models
    "UpdatePassword",
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserUpdateMe",
    # Wallet models
    "WalletCreate",
    "WalletPublic",
    "WalletWithTransactions",
    "TransactionCreate",
    "TransactionPublic",
]
