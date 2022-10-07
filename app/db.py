"""
DB module with database config and declaration.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import settings

db_url = 'postgresql+psycopg2://{}:{}@{}:{}/{}'.format(
    settings.postgres_user, settings.postgres_password,
    settings.postgres_host, settings.postgres_port, settings.postgres_db)
engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Returns db session for use in controllers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
