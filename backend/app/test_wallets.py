"""Tests for wallet and transaction functionality."""

import pytest
from decimal import Decimal

from app.utils import convert_currency, convert_with_fee, calculate_exchange_fee
from app.models import Currency


def test_currency_conversion():
    """Test currency conversion functionality."""
    # Test USD to EUR conversion
    usd_amount = Decimal("100.00")
    eur_amount = convert_currency(usd_amount, Currency.USD, Currency.EUR)
    assert eur_amount == Decimal("85.00")

    # Test EUR to USD conversion
    eur_amount = Decimal("85.00")
    usd_amount = convert_currency(eur_amount, Currency.EUR, Currency.USD)
    assert usd_amount == Decimal("100.00")

    # Test same currency conversion
    same_amount = convert_currency(Decimal("100.00"), Currency.USD, Currency.USD)
    assert same_amount == Decimal("100.00")


def test_exchange_fee_calculation():
    """Test exchange fee calculation."""
    amount = Decimal("100.00")
    fee = calculate_exchange_fee(amount)
    assert fee == Decimal("1.00")  # 1% of 100 = 1


def test_convert_with_fee():
    """Test currency conversion with fee deduction."""
    # USD to EUR with fee
    usd_amount = Decimal("100.00")
    converted_amount, fee = convert_with_fee(usd_amount, Currency.USD, Currency.EUR)

    # 100 USD -> 85 EUR, then 1% fee = 0.85 EUR
    expected_amount = Decimal("84.15")  # 85 - 0.85
    expected_fee = Decimal("0.85")

    assert converted_amount == expected_amount
    assert fee == expected_fee

    # Same currency should have no fee
    same_amount, no_fee = convert_with_fee(usd_amount, Currency.USD, Currency.USD)
    assert same_amount == usd_amount
    assert no_fee == Decimal("0.00")


if __name__ == "__main__":
    test_currency_conversion()
    test_exchange_fee_calculation()
    test_convert_with_fee()
    print("All tests passed!")
