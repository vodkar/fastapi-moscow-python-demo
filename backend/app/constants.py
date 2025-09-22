"""Application constants.

This module groups HTTP status codes, string length limits, and domain-specific
constants for the wallet and transaction functionality (currencies, exchange
rates, fees, and numeric precision settings).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import Final, TypeAlias

# HTTP Status codes
OK_CODE = 200
CREATED_CODE = 201
BAD_REQUEST_CODE = 400
FORBIDDEN_CODE = 403
NOT_FOUND_CODE = 404
CONFLICT_CODE = 409

# String field lengths
EMAIL_MAX_LENGTH = 255
STRING_MAX_LENGTH = 255
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 40
TOKEN_LENGTH = 32


# Wallet and Transaction domain constants


class Currency(StrEnum):
    """Supported currency codes.

    Values are ISO-like currency codes restricted to the application scope.
    """

    USD = "USD"
    EUR = "EUR"
    RUB = "RUB"


class TransactionType(StrEnum):
    """Transaction direction types."""

    CREDIT = "credit"
    DEBIT = "debit"


# Use Decimal for precise money arithmetic. All amounts are quantized to 2 dp.
DECIMAL_QUANT: Final[Decimal] = Decimal("0.01")

# Cross-currency fee as a fraction (e.g., 0.01 == 1%). Applied on converted amount.
CROSS_CURRENCY_FEE_RATE: Final[Decimal] = Decimal("0.01")

# Fixed exchange rates. Mapping of (from_currency, to_currency) -> rate.
# Example: 1 from_currency * rate = to_currency amount (before fees).
ExchangeKey: TypeAlias = tuple[Currency, Currency]
ExchangeRatesMap: TypeAlias = dict[ExchangeKey, Decimal]

EXCHANGE_RATES: Final[ExchangeRatesMap] = {
    # USD base
    (Currency.USD, Currency.USD): Decimal("1.0"),
    (Currency.USD, Currency.EUR): Decimal("0.90"),
    (Currency.USD, Currency.RUB): Decimal("90.0"),
    # EUR base
    (Currency.EUR, Currency.EUR): Decimal("1.0"),
    (Currency.EUR, Currency.USD): Decimal("1.11"),
    (Currency.EUR, Currency.RUB): Decimal("100.0"),
    # RUB base
    (Currency.RUB, Currency.RUB): Decimal("1.0"),
    (Currency.RUB, Currency.USD): Decimal("0.011"),
    (Currency.RUB, Currency.EUR): Decimal("0.010"),
}

# Limits
MAX_WALLETS_PER_USER: Final[int] = 3
