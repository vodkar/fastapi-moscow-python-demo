"""Utility functions for wallet operations."""

from decimal import ROUND_HALF_UP, Decimal

from app.constants import EXCHANGE_FEE_RATE, EXCHANGE_RATES
from app.models import Currency


def convert_currency(
    amount: Decimal,
    from_currency: Currency,
    to_currency: Currency,
) -> Decimal:
    """Convert amount from one currency to another."""
    if from_currency == to_currency:
        return amount

    # Convert to USD first, then to target currency
    usd_amount = amount / Decimal(str(EXCHANGE_RATES[from_currency]))
    target_amount = usd_amount * Decimal(str(EXCHANGE_RATES[to_currency]))

    # Round to 2 decimal places
    return target_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calculate_exchange_fee(amount: Decimal) -> Decimal:
    """Calculate exchange fee for currency conversion."""
    fee = amount * Decimal(str(EXCHANGE_FEE_RATE))
    return fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def convert_with_fee(
    amount: Decimal,
    from_currency: Currency,
    to_currency: Currency,
) -> tuple[Decimal, Decimal]:
    """Convert currency and calculate fee.

    Returns:
        tuple: (converted_amount, fee)

    """
    if from_currency == to_currency:
        return amount, Decimal("0.00")

    converted_amount = convert_currency(amount, from_currency, to_currency)
    fee = calculate_exchange_fee(converted_amount)
    final_amount = converted_amount - fee

    return final_amount, fee
