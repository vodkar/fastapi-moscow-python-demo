"""Currency conversion utilities with fixed exchange rates and fees."""

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

Currency = Literal["USD", "EUR", "RUB"]

# Fixed exchange rates relative to USD for simplicity
RATES: dict[tuple[Currency, Currency], Decimal] = {
    ("USD", "USD"): Decimal("1.0"),
    ("USD", "EUR"): Decimal("0.90"),
    ("USD", "RUB"): Decimal("90.0"),
    ("EUR", "USD"): Decimal("1.1111111111"),  # 1/0.90
    ("EUR", "EUR"): Decimal("1.0"),
    ("EUR", "RUB"): Decimal("100.0"),
    ("RUB", "USD"): Decimal("0.011"),
    ("RUB", "EUR"): Decimal("0.010"),
    ("RUB", "RUB"): Decimal("1.0"),
}

FEE_RATE = Decimal("0.01")  # 1% fee on cross-currency operations


def quantize_money(value: Decimal) -> Decimal:
    """Quantize Decimal to two places using bankers' rounding policy."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def convert(amount: Decimal, from_currency: Currency, to_currency: Currency) -> Decimal:
    """Convert amount between currencies using fixed rates, quantized to 2 decimals."""
    rate = RATES[(from_currency, to_currency)]
    return quantize_money(amount * rate)


def apply_fee(amount: Decimal, *, cross_currency: bool) -> Decimal:
    """Apply a percentage fee if cross-currency conversion is used."""
    if not cross_currency:
        return quantize_money(amount)
    fee = quantize_money(amount * FEE_RATE)
    return quantize_money(amount - fee)
