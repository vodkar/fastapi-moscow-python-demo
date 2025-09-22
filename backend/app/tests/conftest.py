from collections.abc import Generator

import pytest
from app.core.config import settings
from app.core.db import engine, init_db
from app.main import app
from app.models import Item, Transaction, User, Wallet
from app.tests.utils.test_helpers import get_superuser_token_headers
from app.tests.utils.user import authentication_token_from_email
from fastapi.testclient import TestClient
from sqlmodel import Session, delete


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session]:
    with Session(engine) as session:
        init_db(session)
        yield session
        statement = delete(Transaction)
        session.execute(statement)  # type: ignore[deprecated]
        statement = delete(Wallet)
        session.execute(statement)  # type: ignore[deprecated]
        statement = delete(Item)
        session.execute(statement)  # type: ignore[deprecated]
        statement = delete(User)
        session.execute(statement)  # type: ignore[deprecated]
        session.commit()


@pytest.fixture(scope="module")
def client() -> Generator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def superuser_token_headers(client: TestClient) -> dict[str, str]:
    return get_superuser_token_headers(client)


@pytest.fixture(scope="module")
def normal_user_token_headers(client: TestClient, db: Session) -> dict[str, str]:
    return authentication_token_from_email(
        client=client,
        email=settings.EMAIL_TEST_USER,
        db=db,
    )
