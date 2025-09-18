import uuid
from decimal import Decimal

from app.constants import BAD_REQUEST_CODE, CONFLICT_CODE, NOT_FOUND_CODE, OK_CODE
from app.core.config import settings
from fastapi.testclient import TestClient

WALLETS_ENDPOINT = "/wallets/"


def test_create_wallet_and_get(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create USD wallet
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    assert response.status_code == OK_CODE
    data = response.json()
    wallet_id = data["id"]
    assert data["currency"] == "USD"
    assert data["balance"] == "0.00" or float(data["balance"]) == 0.0

    # Read wallet
    response = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == OK_CODE
    data = response.json()
    assert data["currency"] == "USD"


def test_unique_currency_and_limit(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Create three wallets with different currencies
    for cur in ["USD", "EUR", "RUB"]:
        response = client.post(
            f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
            headers=superuser_token_headers,
            json={"currency": cur},
        )
        assert response.status_code == OK_CODE

    # Fourth wallet should fail due to limit
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    # Depending on order, could be conflict (duplicate) or limit; accept either
    assert response.status_code in (CONFLICT_CODE, BAD_REQUEST_CODE)


def test_credit_and_debit(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # Fresh wallet
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    assert response.status_code == OK_CODE
    wallet_id = response.json()["id"]

    # Credit 100 USD
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": "100.00", "type": "credit", "currency": "USD"},
    )
    assert response.status_code == OK_CODE

    # Debit 30 USD
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": "30.00", "type": "debit", "currency": "USD"},
    )
    assert response.status_code == OK_CODE

    # Fetch wallet and verify balance 70.00
    response = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == OK_CODE
    data = response.json()
    assert float(data["balance"]) == 70.0 or data["balance"] == "70.00"


def test_debit_insufficient_funds(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # New wallet
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    assert response.status_code == OK_CODE
    wallet_id = response.json()["id"]

    # Attempt to debit 10 from 0 balance
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": "10.00", "type": "debit", "currency": "USD"},
    )
    assert response.status_code == BAD_REQUEST_CODE


def test_cross_currency_credit_with_fee(
    client: TestClient, superuser_token_headers: dict[str, str]
) -> None:
    # USD wallet
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    assert response.status_code == OK_CODE
    wallet_id = response.json()["id"]

    # Credit 100 EUR to USD wallet
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": "100.00", "type": "credit", "currency": "EUR"},
    )
    assert response.status_code == OK_CODE

    # Expected: 100 EUR -> ~111.11 USD, minus 1% fee -> 110.00 USD
    response = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    )
    data = response.json()
    assert float(data["balance"]) == 110.0 or data["balance"] == "110.00"
