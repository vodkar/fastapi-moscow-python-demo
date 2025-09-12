from decimal import Decimal

from fastapi.testclient import TestClient

from app.constants import BAD_REQUEST_CODE, OK_CODE
from app.core.config import settings

WALLETS_ENDPOINT = "/wallets/"


def _create_wallet(
    client: TestClient, token_headers: dict[str, str], currency: str
) -> dict:
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=token_headers,
        json={"currency": currency},
    )
    assert response.status_code == OK_CODE
    return response.json()


def test_create_wallet(
    superuser_token_headers: dict[str, str],
    client: TestClient,
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "EUR"},
    )
    assert response.status_code == OK_CODE
    data = response.json()
    assert data["currency"] == "EUR"
    assert data["balance"] == 0


def test_prevent_duplicate_currency(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "RUB"},
    )
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "RUB"},
    )
    assert response.status_code == BAD_REQUEST_CODE


def test_credit_transaction(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    wallet_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    ).json()
    wallet_id = wallet_resp["id"]
    tx_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": 50, "type": "credit", "currency": "USD"},
    )
    assert tx_resp.status_code == OK_CODE
    # fetch wallet
    updated_wallet = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    ).json()
    assert Decimal(str(updated_wallet["balance"])) == Decimal("50.00")


def test_debit_transaction(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    wallet_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "EUR"},
    ).json()
    wallet_id = wallet_resp["id"]
    client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": 100, "type": "credit", "currency": "EUR"},
    )
    debit_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": 40, "type": "debit", "currency": "EUR"},
    )
    assert debit_resp.status_code == OK_CODE
    updated_wallet = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    ).json()
    assert Decimal(str(updated_wallet["balance"])) == Decimal("60.00")


def test_overdraft_prevention(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    wallet_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    ).json()
    wallet_id = wallet_resp["id"]
    resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": 10, "type": "debit", "currency": "USD"},
    )
    assert resp.status_code == BAD_REQUEST_CODE


def test_cross_currency_conversion(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    # Scenario: Wallet USD, credit EUR 100 -> convert using rate & fee
    wallet_resp = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    ).json()
    wallet_id = wallet_resp["id"]
    client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}/transactions",
        headers=superuser_token_headers,
        json={"amount": 100, "type": "credit", "currency": "EUR"},
    )
    updated = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet_id}",
        headers=superuser_token_headers,
    ).json()
    # 100 EUR -> USD: 100 /0.9 =111.111.. fee 1% -> 109.999 ~ 110.00 after quantize
    assert Decimal(str(updated["balance"])) == Decimal("110.00")
