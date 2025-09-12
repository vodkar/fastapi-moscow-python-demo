from fastapi.testclient import TestClient

from app.constants import OK_CODE
from app.core.config import settings

WALLETS_ENDPOINT = "/wallets/"


def test_create_wallet(
    client: TestClient,
    superuser_token_headers: dict[str, str],
) -> None:
    response = client.post(
        f"{settings.API_V1_STR}{WALLETS_ENDPOINT}",
        headers=superuser_token_headers,
        json={"currency": "USD"},
    )
    assert response.status_code == OK_CODE
    content = response.json()
    assert content["currency"] == "USD"
    assert content["balance"] == "0.00"
