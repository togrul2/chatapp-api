"""
Config and fixtures for tests.
"""
import os
from typing import Mapping, Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import BASE_DIR
from authentication import create_refresh_token, create_access_token
from main import app as fastapi_app
from db import Base, get_db
from schemas.user import UserCreate
from services.user import UserService

# this is to include backend dir in sys.path
# so that we can import from db, main.py
DB_PATH = BASE_DIR / 'test_db.sqlite3'

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///" + str(DB_PATH)
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
# Use connect_args parameter only with sqlite
SessionTesting = sessionmaker(autocommit=False, autoflush=False,
                              bind=test_engine)


def _get_test_db():
    db = SessionTesting()
    try:
        yield db
    finally:
        db.close()


class _client:
    def __new__(cls,
                app: FastAPI,
                headers: Mapping[str, Any] = None,
                **kwargs):
        __client = TestClient(app, **kwargs)
        __client.headers = headers
        return __client


def pytest_configure(config):  # noqa
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    fastapi_app.dependency_overrides[get_db] = _get_test_db
    Base.metadata.create_all(test_engine)


def pytest_unconfigure(config):
    """Called before test process is exited."""
    Base.metadata.drop_all(test_engine)
    os.remove(DB_PATH)


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


@pytest.fixture()
def client():
    yield _client(fastapi_app)


@pytest.fixture()
def auth_client(auth_tokens):
    yield _client(fastapi_app, headers={
        "Authorization": f"Bearer {auth_tokens['access_token']}"
    })
