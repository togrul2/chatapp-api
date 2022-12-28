"""Config module with settings and global config vars."""
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings

SRC_DIR = Path(__file__).resolve().parent
BASE_DIR = SRC_DIR.parent

load_dotenv(os.path.join(BASE_DIR, ".env"))

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = "HS256"

STATIC_DOMAIN = "http://localhost:8000"
STATIC_URL = "static/"
STATIC_ROOT = SRC_DIR / "static"


class Settings(BaseSettings):
    """Settings for env variables."""

    secret_key: str
    postgres_db: str
    postgres_host: str
    postgres_port: str = "5432"
    postgres_user: str
    postgres_password: str


settings = Settings()
