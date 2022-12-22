"""
DB module with database config and declaration.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

URL_FORMATTER = 'postgresql+psycopg2://{}:{}@{}:{}/{}'

db_url = URL_FORMATTER.format(settings.postgres_user,
                              settings.postgres_password,
                              settings.postgres_host,
                              settings.postgres_port,
                              settings.postgres_db)

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Returns db session for FastAPI dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
