"""
DB module with database config and declaration.
"""
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

URL_FORMATTER = "postgresql+psycopg2://{}:{}@{}:{}/{}"

DB_URL = URL_FORMATTER.format(
    settings.postgres_user,
    settings.postgres_password,
    settings.postgres_host,
    settings.postgres_port,
    settings.postgres_db,
)

engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Returns db session for FastAPI dependency injection."""
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
