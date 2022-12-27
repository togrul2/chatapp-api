"""
DB module with database config and declaration.
"""
from config import settings
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

URL_FORMATTER = "postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

DB_URL = URL_FORMATTER.format(
    user=settings.postgres_user,
    password=settings.postgres_password,
    host=settings.postgres_host,
    port=settings.postgres_port,
    db=settings.postgres_db,
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
