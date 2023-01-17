"""
Config and fixtures for tests.
"""
import asyncio
import os
import shutil

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src import authentication
from src.config import BASE_DIR, settings
from src.dependencies import get_db, get_staticfiles_manager
from src.main import app as fastapi_app
from src.models.user import Friendship, User
from src.staticfiles import LocalStaticFilesManager
from src.utils import parse_url
from tests.async_sql import (
    DBSQLAsyncManager,
    PostgreSQLAsyncManager,
    create_tables,
    drop_tables,
)

params = parse_url(settings.database_url)
db_hostname = params["hostname"]
db_port = params["port"]
db_user = params["user"]
db_password = params["password"]
db_name = params["dbname"]

test_db_name = "test_" + db_name
test_db_url = (
    "postgresql+asyncpg://"
    f"{db_user}:{db_password}@{db_hostname}:{db_port}/{test_db_name}"
)

dbms_session: DBSQLAsyncManager = PostgreSQLAsyncManager(
    db_user, db_password, db_hostname, db_port
)


test_engine = create_async_engine(url=test_db_url)
async_session = sessionmaker(
    test_engine,
    autocommit=False,
    expire_on_commit=False,
    class_=AsyncSession,
    autoflush=False,
)


TEST_STATIC_ROOT = BASE_DIR / "test_static"


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    """Custom event loop fixture. Implemented for making it session scoped."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_teardown():
    """Sets up database and local static files manager.
    Tears down after pytest session is over."""
    await dbms_session.create_database(test_db_name)
    await create_tables(test_engine)
    os.mkdir(TEST_STATIC_ROOT)
    yield
    await drop_tables(test_engine)
    await dbms_session.drop_database(test_db_name)
    shutil.rmtree(TEST_STATIC_ROOT)


@pytest_asyncio.fixture(scope="session")
async def session():
    """Fixture providing Async db session."""
    async with async_session() as db_session:
        yield db_session


@pytest_asyncio.fixture(scope="session")
async def test_app(session: AsyncSession):
    """Test FastAPI app for processing requests.
    Uses testing database and staticfiles manager."""

    def _get_test_db():
        """Testing dependency for getting db session."""
        yield session

    def _get_test_staticfiles_manager():
        """Testing dependency for staticfiles manager."""
        return LocalStaticFilesManager(
            "http://localhost:8000", "/static/", TEST_STATIC_ROOT
        )

    fastapi_app.dependency_overrides[get_db] = _get_test_db
    fastapi_app.dependency_overrides[
        get_staticfiles_manager
    ] = _get_test_staticfiles_manager

    yield fastapi_app


@pytest.fixture(scope="session")
def client(test_app: FastAPI):
    """Client for testings endpoints."""
    yield AsyncClient(app=test_app, base_url="http://test")


@pytest_asyncio.fixture()
async def auth_client(user: User, client: AsyncClient):
    """Client of authorized user for testings endpoints."""
    access_token = authentication.create_access_token(user.id)
    client.headers = {"Authorization": f"Bearer {access_token}"}
    yield client


@pytest_asyncio.fixture()
async def user(session: AsyncSession):
    """Fixture for generating user"""
    password = authentication.get_hashed_password("Testpassword")
    user_model = User(
        username="johndoe",
        email="johndoe@example.com",
        first_name="John",
        last_name="Doe",
        password=password,
    )
    session.add(user_model)
    await session.commit()
    target_id = user_model.id
    yield user_model
    await session.execute(delete(User).where(User.id == target_id))
    await session.commit()


@pytest_asyncio.fixture()
async def sender_user(session: AsyncSession):
    """User for sending friendship request to another one."""
    password = authentication.get_hashed_password("Testpassword")
    user_model = User(
        username="peterdoe",
        email="peterdoe@example.com",
        first_name="Peter",
        last_name="Doe",
        password=password,
    )
    session.add(user_model)
    await session.commit()
    target_id = user_model.id
    yield user_model
    await session.execute(delete(User).where(User.id == target_id))
    await session.commit()


@pytest_asyncio.fixture()
async def friendship_request(user: User, sender_user: User, session):
    """Friendship request model fixture."""

    friendship_model = Friendship(
        receiver_id=user.id, sender_id=sender_user.id
    )
    session.add(friendship_model)
    await session.commit()
    target_id = friendship_model.id
    yield friendship_model
    await session.execute(delete(Friendship).where(Friendship.id == target_id))
    await session.commit()


@pytest_asyncio.fixture()
async def friendship(session: AsyncSession, friendship_request: Friendship):
    """Friendship fixture between user and sender_user."""
    query = (
        update(Friendship)
        .where(Friendship.id == friendship_request.id)
        .values(accepted=True)
    )
    await session.execute(query)
    await session.commit()
    yield friendship_request
