"""
Config and fixtures for tests.
"""
import shutil
from typing import Any, Mapping

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from authentication import create_access_token
from config import SRC_DIR, settings
from db import URL_FORMATTER, get_db
from main import app as fastapi_app
from models.user import User
from schemas.user import UserCreate
from services.friendship import FriendshipService
from services.user import UserService
from staticfiles import LocalStaticFilesManager, get_staticfiles_manager
from tests.sql import PostgreSQLSession, create_tables, drop_tables
from utils import SingletonMeta

test_db_name = "test_" + settings.postgres_db
test_db_url = URL_FORMATTER.format(
    user=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    db=test_db_name,
)


db_session = PostgreSQLSession(
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
    db = TestDatabase(test_db_url).session_maker()
    try:
        yield db
    finally:
        db.close()


TEST_STATIC_ROOT = SRC_DIR / "test_static"


def _get_static_handler():
    return LocalStaticFilesManager(
        "http://localhost:8000", "static/", TEST_STATIC_ROOT
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
    db_session.create_database(test_db_name)
    create_tables(TestDatabase(test_db_url).test_engine)

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    fastapi_app.dependency_overrides[
        get_staticfiles_manager
    ] = _get_static_handler


def pytest_unconfigure(config):  # noqa
    """Called before test process is exited."""
    drop_tables(TestDatabase(test_db_url).test_engine)
    db_session.drop_database(test_db_name)
    shutil.rmtree(TEST_STATIC_ROOT)


user_password = "Testpassword"


@pytest.fixture()
def user():
    with TestDatabase(test_db_url).session_maker() as session:
        user_service = UserService(session)
        user = user_service.create(
            UserCreate.construct(
                username="johndoe",
                email="johndoe@example.com",
                first_name="John",
                last_name="Doe",
                password=user_password,
            )
        )
        yield user
        user_service.delete(user.id)


@pytest.fixture()
def client():
    """Client for testings endpoints."""
    yield ClientFactory(fastapi_app, {})


@pytest.fixture()
def auth_client(user: User):
    """Client of authorized user for testings endpoints."""
    access_token = create_access_token(user.id)  # type: ignore
    yield ClientFactory(
        fastapi_app, headers={"Authorization": "Bearer %s" % access_token}
    )


@pytest.fixture()
def sender_user():
    """User for sending friendship request to another one."""
    with TestDatabase(test_db_url).session_maker() as session:
        user_password = "Testpassword"

        user_services = UserService(session)
        user = user_services.create(
            UserCreate.construct(
                username="peterdoe",
                email="peterdoe@example.com",
                first_name="Peter",
                last_name="Doe",
                password=user_password,
            )
        )
        yield user
        user_services.delete(user.id)


@pytest.fixture()
def friendship_request(user: User, sender_user: User):
    """Friendship model factory."""
    with TestDatabase(test_db_url).session_maker() as session:
        service = FriendshipService(session, sender_user.id)  # type: ignore
        friendship = service.send_to(user.id)  # type: ignore
        yield friendship
        service.delete(friendship.id)
