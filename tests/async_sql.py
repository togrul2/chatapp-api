from abc import ABC, abstractmethod
from collections.abc import Coroutine, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from asyncpg import connect
from sqlalchemy.ext.asyncio import AsyncEngine

from src.db import Base


class DBSQLAsyncSession(ABC):
    """Abstract class for db connection management."""

    @abstractmethod
    async def get_connection(self):
        """Context manager which returns async connection.
        Must be decorated with @asynccontextmanager"""

    @abstractmethod
    async def run_commands(self, *commands) -> Coroutine[Any, Any, None]:
        """Runs SQL commands in connection."""

    @abstractmethod
    async def create_database(self, db_name: str) -> Coroutine[Any, Any, None]:
        """Creates database with given name."""

    @abstractmethod
    async def drop_database(self, db_name: str) -> Coroutine[Any, Any, None]:
        """Creates database with given name."""


@dataclass
class PostgreSQLAsyncSession(DBSQLAsyncSession):
    username: str
    password: str
    host: str
    port: str

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for opening database session."""
        conn = await connect(
            user=self.username,
            host=self.host,
            port=self.port,
            password=self.password,
        )
        yield conn
        await conn.close()

    async def run_commands(self, *commands: Sequence[str]):
        """Runs given command in database.
        Raises error if not connection is established"""

        async with self.get_connection() as conn:
            for command in commands:
                await conn.execute(*command)

    async def create_database(self, db_name: str) -> None:
        """Creates the given database."""
        await self.run_commands(
            (f'CREATE DATABASE "{db_name}" ',),
        )
        print("Test database created")

    async def drop_database(self, db_name: str) -> None:
        """Drops the given database."""

        await self.run_commands(
            (f'ALTER DATABASE "{db_name}" allow_connections = off',),
            (
                "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                "FROM pg_stat_activity "
                f"WHERE pg_stat_activity.datname = '{db_name}' "
                "AND pid <> pg_backend_pid()",
            ),
            (f'DROP DATABASE "{db_name}"',),
        )
        print("Test database dropped")


async def create_tables(test_engine: AsyncEngine) -> None:
    """Creates all the tables in the binded to the engine database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(test_engine: AsyncEngine) -> None:
    """Drops all the tables in the binded to the engine database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
