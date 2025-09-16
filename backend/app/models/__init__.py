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

# Transaction models
from app.models.transaction_models import (
    TransactionBase,
    TransactionCreate,
    TransactionPublic,
    TransactionsPublic,
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
from app.models.wallet_details_models import TransactionInWallet, WalletWithTransactions

# Wallet models
from app.models.wallet_models import (
    WalletBase,
    WalletCreate,
    WalletPublic,
    WalletsPublic,
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
    "Transaction",
    "User",
    "Wallet",
    # Item models
    "ItemBase",
    "ItemCreate",
    "ItemPublic",
    "ItemsPublic",
    "ItemUpdate",
    # Transaction models
    "TransactionBase",
    "TransactionCreate",
    "TransactionPublic",
    "TransactionsPublic",
    # User models
    "UpdatePassword",
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserUpdateMe",
    # Wallet models
    "WalletBase",
    "WalletCreate",
    "WalletPublic",
    "WalletsPublic",
    "TransactionInWallet",
    "WalletWithTransactions",
]
