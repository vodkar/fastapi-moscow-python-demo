"""Currency conversion service with fixed exchange rates."""

from decimal import Decimal
from typing import Final

from app.models.db_models import CurrencyEnum

# Fixed exchange rates (base currency: USD)
EXCHANGE_RATES: Final[dict[CurrencyEnum, Decimal]] = {
    CurrencyEnum.USD: Decimal("1.00"),
    CurrencyEnum.EUR: Decimal("0.85"),
    CurrencyEnum.RUB: Decimal("75.00"),
}

# Transaction fees for currency conversion (percentage)
CONVERSION_FEE_RATE: Final[Decimal] = Decimal("0.02")  # 2%


def convert_currency(
    amount: Decimal, from_currency: CurrencyEnum, to_currency: CurrencyEnum
) -> Decimal:
    """Convert amount from one currency to another using fixed exchange rates."""
    if from_currency == to_currency:
        return amount

    # Convert to USD first (base currency)
    usd_amount = amount / EXCHANGE_RATES[from_currency]

    # Convert from USD to target currency
    converted_amount = usd_amount * EXCHANGE_RATES[to_currency]

    return converted_amount.quantize(Decimal("0.01"))


def calculate_conversion_fee(amount: Decimal) -> Decimal:
    """Calculate conversion fee for cross-currency transactions."""
    fee = amount * CONVERSION_FEE_RATE
    return fee.quantize(Decimal("0.01"))


def convert_with_fee(
    amount: Decimal, from_currency: CurrencyEnum, to_currency: CurrencyEnum
) -> tuple[Decimal, Decimal]:
    """Convert currency amount and return converted amount and fee."""
    if from_currency == to_currency:
        return amount, Decimal("0.00")

    converted_amount = convert_currency(amount, from_currency, to_currency)
    fee = calculate_conversion_fee(converted_amount)
    final_amount = converted_amount - fee

    return final_amount.quantize(Decimal("0.01")), fee
