"""
Config and fixtures for tests.
"""
from typing import Mapping, Any, Sequence

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg2 import connect, extensions
from psycopg2.sql import Identifier, SQL
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import settings, BASE_DIR
from authentication import create_refresh_token, create_access_token
from main import app as fastapi_app
from db import Base, get_db, URL_FORMATTER
from schemas.user import UserCreate
from services.user import UserService
from staticfiles import LocalStaticFilesManager, get_staticfiles_manager
from utils import SingletonMeta

test_db_name = 'test_' + settings.postgres_db
test_db_url = URL_FORMATTER.format(
    settings.postgres_user, settings.postgres_password,
    settings.postgres_host, settings.postgres_port, test_db_name
)


class TestDatabase(metaclass=SingletonMeta):
    """Singleton class provides test database engine and sessionmaker."""

    def __init__(self, db_name: str = test_db_name, db_url: str = test_db_url):
        self.create_database(db_name)
        self.test_engine = create_engine(db_url)
        self.session_maker = sessionmaker(bind=self.test_engine)

    @staticmethod
    def run_sql_commands(*commands: Sequence[Any]):
        conn = connect(
            user=settings.postgres_user,
            host=settings.postgres_host,
            port=settings.postgres_port,
            password=settings.postgres_password)
        conn.autocommit = True
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        for command in commands:
            cursor.execute(*command)
        cursor.close()
        conn.close()

    def create_database(self, db_name: str):
        self.run_sql_commands(
            (SQL('CREATE DATABASE {}').format(Identifier(db_name)),)
        )

    def create_tables(self) -> None:
        Base.metadata.create_all(self.test_engine)

    def drop_tables(self) -> None:
        Base.metadata.drop_all(self.test_engine)

    def drop_database(self) -> None:
        self.run_sql_commands(
            (SQL('ALTER DATABASE {} allow_connections = off').format(
                Identifier(test_db_name)),),
            (SQL('SELECT pg_terminate_backend(pg_stat_activity.pid) '
                 'FROM pg_stat_activity '
                 'WHERE pg_stat_activity.datname = %s '
                 'AND pid <> pg_backend_pid()'
                 ), ('test_chatapp',)),
            (SQL('DROP DATABASE {}').format(Identifier(test_db_name)),)
        )


def _get_test_db():
    db = TestDatabase().session_maker()
    try:
        yield db
    finally:
        db.close()


STATIC_ROOT = BASE_DIR / 'app' / 'test_static'


def _get_static_handler():
    return LocalStaticFilesManager('http://localhost:8000', 'static/',
                                   STATIC_ROOT)


class ClientFactory:
    """Client factory class."""
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
    fastapi_app.dependency_overrides[get_staticfiles_manager] = _get_static_handler
    TestDatabase().create_tables()


def pytest_unconfigure(config):  # noqa
    """Called before test process is exited."""
    TestDatabase().drop_tables()
    TestDatabase().drop_database()


user_password = 'Testpassword'


@pytest.fixture()
def user():
    with TestDatabase().session_maker() as session:
        user_service = UserService(session)
        user = user_service.create(UserCreate.construct(
            username='johndoe',
            email='johndoe@example.com',
            first_name='John',
            last_name='Doe',
            password=user_password
        ))
        yield user
        user_service.delete(user.id)


@pytest.fixture()
def client():
    """Client for testings endpoints."""
    yield ClientFactory(fastapi_app)


@pytest.fixture()
def auth_client(user):
    """Client of authorized user for testings endpoints."""
    access_token = create_access_token(user.id)
    yield ClientFactory(fastapi_app, headers={
        'Authorization': 'Bearer %s' % access_token
    })
