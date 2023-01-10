"""
DB module with database configs and declarations.
"""
from aioredis import Redis
from aioredis.exceptions import ConnectionError as RedisConnectionError
from broadcaster import Broadcast
from psycopg2 import OperationalError, connect
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

import utils
from config import settings

# PostgreSQL
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Broadcaster-Redis
broadcast = Broadcast(settings.redis_url)


def ping_sql_database():
    """Pings SQL DB in order to make sure it is running"""
    params = utils.parse_url(settings.database_url)
    try:
        connection = connect(
            dbname=params["dbname"],
            user=params["user"],
            password=params["password"],
            host=params["hostname"],
            port=params["port"],
        )
        connection.close()
    except OperationalError as ext:
        raise OperationalError(
            "Cannot connect to sql database. "
            "Are you sure that db is up and running at "
            f"{settings.postgres_host} on port {settings.postgres_port}?"
        ) from ext


async def ping_redis_database():
    """Pings redis server in order to make sure that it is up and running."""
    try:
        server = Redis()
        await server.ping()
        await server.close()

    except RedisConnectionError as ext:
        raise RedisConnectionError(
            "Cannot connect to redis server. "
            "Are you sure that it is up and running at "
            f"{settings.redis_url}?"
        ) from ext
