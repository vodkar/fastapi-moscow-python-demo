import uuid
from decimal import Decimal

from app.constants import BAD_REQUEST_CODE, CREATED_CODE, NOT_FOUND_CODE, OK_CODE
from app.core.config import settings
from app.models import Currency, Wallet
from app.tests.utils.user import create_random_user
from app.tests.utils.wallet import create_random_wallet, create_wallet_with_balance
from fastapi.testclient import TestClient
from sqlmodel import Session

# Constants for commonly used strings
WALLETS_ENDPOINT = "/wallets/"
ERROR_DETAIL_KEY = "detail"


def test_create_wallet(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    wallet_data = {"currency": "USD"}
    response = client.post(
        f"{settings.API_V1_STR}/users/{user.id}/wallets/",
        headers=superuser_token_headers,
        json=wallet_data,
    )
    assert response.status_code == CREATED_CODE
    response_content = response.json()
    assert response_content["currency"] == "USD"
    assert response_content["balance"] == 0.0
    assert response_content["user_id"] == str(user.id)
    assert "id" in response_content


def test_create_wallet_duplicate_currency(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    # Create first wallet
    create_random_wallet(db, user_id=user.id, currency=Currency.USD)

    # Try to create another wallet with same currency
    wallet_data = {"currency": "USD"}
    response = client.post(
        f"{settings.API_V1_STR}/users/{user.id}/wallets/",
        headers=superuser_token_headers,
        json=wallet_data,
    )
    assert response.status_code == BAD_REQUEST_CODE


def test_create_wallet_invalid_currency(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    wallet_data = {"currency": "INVALID"}
    response = client.post(
        f"{settings.API_V1_STR}/users/{user.id}/wallets/",
        headers=superuser_token_headers,
        json=wallet_data,
    )
    assert response.status_code == 422  # Validation error


def test_get_wallet(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    wallet = create_wallet_with_balance(db, balance=50.0)
    response = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{wallet.id}",
        headers=superuser_token_headers,
    )
    assert response.status_code == OK_CODE
    response_content = response.json()
    assert response_content["id"] == str(wallet.id)
    assert response_content["balance"] == 50.0
    assert response_content["currency"] == wallet.currency.value


def test_get_wallet_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}{uuid.uuid4()}",
        headers=superuser_token_headers,
    )
    assert response.status_code == NOT_FOUND_CODE


def test_get_user_wallets(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    user = create_random_user(db)
    create_random_wallet(db, user_id=user.id, currency=Currency.USD)
    create_random_wallet(db, user_id=user.id, currency=Currency.EUR)

    response = client.get(
        f"{settings.API_V1_STR}/users/{user.id}/wallets/",
        headers=superuser_token_headers,
    )
    assert response.status_code == OK_CODE
    response_content = response.json()
    assert len(response_content) == 2


def test_get_user_wallets_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/users/{uuid.uuid4()}/wallets/",
        headers=superuser_token_headers,
    )
    assert response.status_code == NOT_FOUND_CODE
