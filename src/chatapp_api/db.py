"""
DB module with database configs and declarations.
"""
from aioredis import Redis
from aioredis.exceptions import ConnectionError as RedisConnectionError
from asyncpg import connect
from broadcaster import Broadcast  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.chatapp_api import utils
from src.chatapp_api.config import settings

# PostgreSQL
engine = create_async_engine(settings.database_url)
async_session = sessionmaker(
    autocommit=False,
    expire_on_commit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
)
Base = declarative_base()

# Broadcaster-Redis
broadcaster = Broadcast(settings.messaging_url)


async def ping_sql_database():
    """Pings SQL DB in order to make sure it is running"""
    params = utils.parse_url(settings.database_url)
    try:
        connection = await connect(
            database=params["dbname"],
            user=params["user"],
            password=params["password"],
            host=params["hostname"],
            port=params["port"],
        )
        await connection.close()
    except ConnectionRefusedError as ext:
        raise ConnectionRefusedError(
            "Cannot connect to sql database. "
            "Are you sure that db is up and running at "
            f"{params['hostname']} on port {params['port']}?"
        ) from ext


async def ping_redis_database():
    """Pings redis server in order to make sure that it is up and running."""
    params = utils.parse_url(settings.messaging_url)

    try:
        server = Redis(
            host=params["hostname"],
            port=params["port"],
            username=params["user"],
            password=params["password"],
        )
        await server.ping()
        await server.close()

    except RedisConnectionError as ext:
        raise RedisConnectionError(
            "Cannot connect to redis server. "
            "Are you sure that it is up and running at "
            f"{settings.messaging_url}?"
        ) from ext
