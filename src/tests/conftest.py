"""
Config and fixtures for tests.
"""
import shutil
from collections.abc import Mapping
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import authentication
from authentication import create_access_token
from config import BASE_DIR, settings
from dependencies import get_db, get_staticfiles_manager
from main import app as fastapi_app
from models.user import Friendship, User
from staticfiles import LocalStaticFilesManager
from tests.sql import (
    DBSQLSession,
    PostgreSQLSession,
    create_tables,
    drop_tables,
)
from utils import SingletonMeta

test_db_name = "test_" + settings.postgres_db
test_db_url = (
    f"postgresql+psycopg2://"
    f"{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}"
    f"/{test_db_name}"
)

dbms_session: DBSQLSession = PostgreSQLSession(
    settings.postgres_user,
    settings.postgres_password,
    settings.postgres_host,
    settings.postgres_port,
)


class TestDatabase(metaclass=SingletonMeta):
    """Singleton class provides test database engine and sessionmaker."""

    def __init__(self, db_url: str):
        self.test_engine = create_engine(url=db_url)
        self.session_maker = sessionmaker(bind=self.test_engine)


def _get_test_db():
    db_session = TestDatabase(test_db_url).session_maker()
    try:
        yield db_session
    finally:
        db_session.close()


TEST_STATIC_ROOT = BASE_DIR / "test_static"


def _get_test_staticfiles_manager():
    return LocalStaticFilesManager(
        "http://localhost:8000", "/static/", TEST_STATIC_ROOT
    )


class ClientFactory:
    """Client factory class."""

    def __new__(cls, app: FastAPI, headers: Mapping[str, Any], **kwargs):
        _client = TestClient(app, **kwargs)
        _client.headers = headers  # type: ignore
        return _client


def pytest_configure(config):  # noqa
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    dbms_session.create_database(test_db_name)
    create_tables(TestDatabase(test_db_url).test_engine)

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    fastapi_app.dependency_overrides[
        get_staticfiles_manager
    ] = _get_test_staticfiles_manager


def pytest_unconfigure(config):  # noqa
    """Called before test process is exited."""
    drop_tables(TestDatabase(test_db_url).test_engine)
    dbms_session.drop_database(test_db_name)
    shutil.rmtree(TEST_STATIC_ROOT)


@pytest.fixture()
def user():
    """Fixture for generating user"""
    with TestDatabase(test_db_url).session_maker() as session:
        password = authentication.get_hashed_password("Testpassword")
        user_model = User(
            username="johndoe",
            email="johndoe@example.com",
            first_name="John",
            last_name="Doe",
            password=password,
        )
        session.add(user_model)
        session.commit()
        target_id = user_model.id
        yield user_model

        session.query(User).filter(User.id == target_id).delete()
        session.commit()


@pytest.fixture()
def client():
    """Client for testings endpoints."""
    yield ClientFactory(fastapi_app, {})


@pytest.fixture()
def auth_client(user: User):
    """Client of authorized user for testings endpoints."""
    access_token = create_access_token(user.id)
    yield ClientFactory(
        fastapi_app, headers={"Authorization": f"Bearer {access_token}"}
    )


@pytest.fixture()
def sender_user():
    """User for sending friendship request to another one."""
    with TestDatabase(test_db_url).session_maker() as session:
        password = authentication.get_hashed_password("Testpassword")
        user_model = User(
            username="peterdoe",
            email="peterdoe@example.com",
            first_name="Peter",
            last_name="Doe",
            password=password,
        )
        session.add(user_model)
        session.commit()
        target_id = user_model.id
        yield user_model

        session.query(User).filter(User.id == target_id).delete()
        session.commit()


@pytest.fixture()
def friendship_request(user: User, sender_user: User):
    """Friendship model factory."""
    with TestDatabase(test_db_url).session_maker() as session:
        friendship_model = Friendship(
            receiver_id=user.id, sender_id=sender_user.id
        )
        session.add(friendship_model)
        session.commit()
        target_id = friendship_model.id
        yield friendship_model

        session.query(Friendship).filter(Friendship.id == target_id).delete()
        session.commit()
