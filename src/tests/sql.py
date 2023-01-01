"""
Module with sql utils for running sql code.
This is required to create test database, tables etc.
"""
from abc import ABC, abstractmethod
from collections.abc import Sequence
from contextlib import contextmanager
from dataclasses import dataclass

from psycopg2 import connect, extensions
from psycopg2.sql import SQL, Composed, Identifier

from db import Base


class DBSQLSession(ABC):
    """Abstract class for db connection management."""

    @abstractmethod
    @contextmanager
    def session(self):
        """Context manager for providing session with DBMS."""
        yield

    @abstractmethod
    @contextmanager
    def cursor(self):
        """Context manager for providing cursor with connection."""
        yield

    @abstractmethod
    def run_commands(self, *commands) -> None:
        """Runs SQL commands in connection."""


@dataclass
class PostgreSQLSession(DBSQLSession):
    """Class for establishing session with database."""

    username: str
    password: str
    host: str
    port: str

    @contextmanager
    def session(self):
        """Context manager for opening database session."""

        conn = connect(
            user=self.username,
            host=self.host,
            port=self.port,
            password=self.password,
        )
        conn.autocommit = True
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        yield conn
        conn.close()

    @contextmanager
    def cursor(self):
        """Context manager for opening database session cursor."""

        with self.session() as session:
            cursor = session.cursor()
            yield cursor
            cursor.close()

    def run_commands(
        self, *commands: tuple[SQL, Sequence[str]] | Sequence[Composed]
    ):
        """Runs given command in database.
        Raises error if not connection is established"""

        with self.cursor() as cursor:
            for cmd in commands:
                cursor.execute(*cmd)  # type: ignore

    def create_database(self, db_name: str) -> None:
        """Creates the given database."""

        self.run_commands(
            (SQL("CREATE DATABASE {}").format(Identifier(db_name)),)
        )
        print("Test database created")

    def drop_database(self, db_name: str) -> None:
        """Drops the given database."""

        self.run_commands(
            (
                SQL("ALTER DATABASE {} allow_connections = off").format(
                    Identifier(db_name)
                ),
            ),
            (
                SQL(
                    "SELECT pg_terminate_backend(pg_stat_activity.pid) "
                    "FROM pg_stat_activity "
                    "WHERE pg_stat_activity.datname = %s "
                    "AND pid <> pg_backend_pid()"
                ),
                ("test_chatapp",),
            ),
            (SQL("DROP DATABASE {}").format(Identifier(db_name)),),
        )
        print("Test database dropped")


def create_tables(test_engine) -> None:
    """Creates all the tables in the binded to the engine database."""
    Base.metadata.create_all(test_engine)  # type: ignore


def drop_tables(test_engine) -> None:
    """Drops all the tables in the binded to the engine database."""
    Base.metadata.drop_all(test_engine)  # type: ignore
