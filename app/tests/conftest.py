"""
Config and fixtures for tests.
"""
import os
import sys
from typing import Any
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import BASE_DIR
from jwt import create_refresh_token, create_access_token
from main import app as fastapi_app
from db import Base, get_db
from schemas import UserCreate
from services import UserService

# this is to include backend dir in sys.path
# so that we can import from db, main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_db.sqlite3"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
# Use connect_args parameter only with sqlite
SessionTesting = sessionmaker(autocommit=False, autoflush=False,
                              bind=test_engine)


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """
    Base.metadata.create_all(test_engine)  # Create the tables.
    yield fastapi_app
    Base.metadata.drop_all(test_engine)  # Drop tables.


@pytest.fixture(scope="function")
def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
    connection = test_engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    yield session  # use the session in tests.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(
        app: FastAPI, db_session: SessionTesting
) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture
    to override the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as _client:
        yield _client


def pytest_unconfigure(config):
    """Called before test process is exited."""
    os.remove(BASE_DIR / "app" / "tests" / "test_db.sqlite3")


user_password = "Testpassword"


@pytest.fixture(scope="function")
def user():
    with SessionTesting() as session:
        user_service = UserService(session)
        user = user_service.create(UserCreate.construct(
            username="johndoe",
            email="johndoe@example.com",
            first_name="John",
            last_name="Doe",
            password=user_password
        ))
        yield user
        user_service.delete(user.id)


@pytest.fixture(scope="function")
def auth_tokens(user):
    yield {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id)
    }


@pytest.fixture(scope="function")
def auth_client(app, db_session, auth_tokens):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as _client:
        _client.headers = {
            "Authorization": f"Bearer {auth_tokens['access_token']}"
        }
        yield _client
