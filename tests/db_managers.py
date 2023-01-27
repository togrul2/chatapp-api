"""Async managers for SQL databases."""
from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass

from asyncpg import Connection, connect
from sqlalchemy.ext.asyncio import AsyncEngine

from src.db import Base


@dataclass
class AsyncConnectionManager:
    host: str
    port: int
    user: str
    password: str

    async def __aenter__(self) -> Connection:
        self.conn = await connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
        )
        return self.conn

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.conn.close()


@dataclass
class DBSQLAsyncManager(ABC):
    """Abstract class (aka interface) for db managers."""

    username: str
    password: str
    host: str
    port: int
    test_db_name: str

    @abstractmethod
    async def _run_commands(self, *commands) -> None:
        """Runs SQL commands in connection."""

    @abstractmethod
    async def create_database(self) -> None:
        """Creates database with given name."""

    @abstractmethod
    async def drop_database(self) -> None:
        """Creates database with given name."""


@dataclass
class PostgreSQLAsyncManager(DBSQLAsyncManager):
    """Asynchronous PostgreSQL connection & management class."""

    async def _run_commands(self, *commands: Sequence[str]) -> None:
        """Runs given command in database.
        Raises error if no connection is established."""

        async with AsyncConnectionManager(
            self.host, self.port, self.username, self.password
        ) as conn:
            for command in commands:
                await conn.execute(*command)

    async def create_database(self) -> None:
        """Creates the given database."""
        await self._run_commands(
            (f'CREATE DATABASE "{self.test_db_name}" ',),
        )
        print("\nTest database created.\n")

    async def drop_database(self) -> None:
        """Drops the given database."""

        await self._run_commands(
            (f'ALTER DATABASE "{self.test_db_name}" allow_connections = off',),
            (
                "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                "FROM pg_stat_activity "
                "WHERE pg_stat_activity.datname = $1 "
                "AND pid <> pg_backend_pid()",
                self.test_db_name,
            ),
            (f'DROP DATABASE "{self.test_db_name}"',),
        )
        print("\nTest database dropped.\n")


async def create_tables(test_engine: AsyncEngine) -> None:
    """Creates all the tables in the binded to the engine database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables(test_engine: AsyncEngine) -> None:
    """Drops all the tables in the binded to the engine database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
