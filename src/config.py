"""Config module with settings and global config vars."""
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings

# Directories
SRC_DIR = Path(__file__).resolve().parent  # /src
BASE_DIR = SRC_DIR.parent

load_dotenv(BASE_DIR / ".env")

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = "HS256"

# staticfiles
STATIC_DOMAIN = "http://localhost:8000"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "static"


class Settings(BaseSettings):
    """Settings for env variables."""

    secret_key: str
    database_url: str

    postgres_db: str
    postgres_host: str
    postgres_port: str = "5432"
    postgres_user: str
    postgres_password: str


settings = Settings()  # type: ignore
