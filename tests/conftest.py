"""
Config and fixtures for tests.
"""
import asyncio
import os
import shutil
from typing import cast

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, Headers
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.chatapp_api.auth.jwt import create_access_token, password_context
from src.chatapp_api.config import BASE_DIR, settings
from src.chatapp_api.dependencies import (
    get_db_session,
    get_staticfiles_manager,
)
from src.chatapp_api.friendship.models import Friendship
from src.chatapp_api.main import app as fastapi_app
from src.chatapp_api.staticfiles import LocalStaticFilesManager
from src.chatapp_api.user.models import User
from src.chatapp_api.utils import parse_url
from tests.db_managers import (
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
    cast(str, db_user),
    cast(str, db_password),
    cast(str, db_hostname),
    cast(int, db_port),
    test_db_name,
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
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_teardown():
    """Sets up database and local static files manager.
    Tears down after pytest session is over."""
    await dbms_session.create_database()
    await create_tables(test_engine)
    os.mkdir(TEST_STATIC_ROOT)
    yield
    await drop_tables(test_engine)
    await dbms_session.drop_database()
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

    fastapi_app.dependency_overrides[get_db_session] = _get_test_db
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
    access_token = create_access_token(cast(int, user.id))
    client.headers = Headers({"Authorization": f"Bearer {access_token}"})
    yield client


@pytest_asyncio.fixture()
async def user(session: AsyncSession):
    """Fixture for generating user"""
    password = password_context.hash("Testpassword")
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
    password = password_context.hash("Testpassword")
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
async def friendship_request(
    user: User, sender_user: User, session: AsyncSession
):
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
async def friendship(user: User, sender_user: User, session: AsyncSession):
    """Friendship fixture between user and sender_user."""
    friendship_model = Friendship(
        receiver_id=user.id, sender_id=sender_user.id, accepted=True
    )
    session.add(friendship_model)
    await session.commit()
    target_id = friendship_model.id
    yield friendship_model
    await session.execute(delete(Friendship).where(Friendship.id == target_id))
    await session.commit()
