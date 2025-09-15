import uuid
from decimal import Decimal

from app.constants import BAD_REQUEST_CODE, CREATED_CODE, NOT_FOUND_CODE, OK_CODE
from app.core.config import settings
from app.models import Currency, Transaction, TransactionType
from app.tests.utils.user import create_random_user
from app.tests.utils.wallet import create_wallet_with_balance
from fastapi.testclient import TestClient
from sqlmodel import Session

# Constants for commonly used strings
TRANSACTIONS_ENDPOINT = "/transactions/"
ERROR_DETAIL_KEY = "detail"


def test_create_credit_transaction(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    wallet = create_wallet_with_balance(db, balance=0.0)
    transaction_data = {
        "wallet_id": str(wallet.id),
        "amount": 100.0,
        "type": "credit",
        "description": "Test credit",
    }
    response = client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )
    assert response.status_code == CREATED_CODE
    response_content = response.json()
    assert response_content["amount"] == 100.0
    assert response_content["type"] == "credit"
    assert response_content["wallet_id"] == str(wallet.id)
    assert "id" in response_content


def test_create_debit_transaction(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    wallet = create_wallet_with_balance(db, balance=100.0)
    transaction_data = {
        "wallet_id": str(wallet.id),
        "amount": 50.0,
        "type": "debit",
        "description": "Test debit",
    }
    response = client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )
    assert response.status_code == CREATED_CODE
    response_content = response.json()
    assert response_content["amount"] == 50.0
    assert response_content["type"] == "debit"


def test_create_debit_transaction_insufficient_funds(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    wallet = create_wallet_with_balance(db, balance=10.0)
    transaction_data = {
        "wallet_id": str(wallet.id),
        "amount": 50.0,
        "type": "debit",
        "description": "Test insufficient funds",
    }
    response = client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )
    assert response.status_code == BAD_REQUEST_CODE
    response_content = response.json()
    assert "insufficient funds" in response_content[ERROR_DETAIL_KEY].lower()


def test_create_transaction_wallet_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    transaction_data = {
        "wallet_id": str(uuid.uuid4()),
        "amount": 50.0,
        "type": "credit",
        "description": "Test with non-existent wallet",
    }
    response = client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )
    assert response.status_code == NOT_FOUND_CODE


def test_get_wallet_transactions(
    client: TestClient,
    superuser_token_headers: dict[str, str],
    db: Session,
) -> None:
    wallet = create_wallet_with_balance(db, balance=100.0)

    # Create a credit transaction
    transaction_data = {
        "wallet_id": str(wallet.id),
        "amount": 50.0,
        "type": "credit",
        "description": "Test credit",
    }
    client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )

    # Create a debit transaction
    transaction_data = {
        "wallet_id": str(wallet.id),
        "amount": 25.0,
        "type": "debit",
        "description": "Test debit",
    }
    client.post(
        f"{settings.API_V1_STR}{TRANSACTIONS_ENDPOINT}",
        headers=superuser_token_headers,
        json=transaction_data,
    )

    # Get wallet transactions
    response = client.get(
        f"{settings.API_V1_STR}/wallets/{wallet.id}/transactions/",
        headers=superuser_token_headers,
    )
    assert response.status_code == OK_CODE
    response_content = response.json()
    assert len(response_content) == 2


def test_get_wallet_transactions_not_found(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.get(
        f"{settings.API_V1_STR}/wallets/{uuid.uuid4()}/transactions/",
        headers=superuser_token_headers,
    )
    assert response.status_code == NOT_FOUND_CODE
