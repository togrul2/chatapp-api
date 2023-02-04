"""Config module with settings and global config vars."""
import os
from pathlib import Path
from typing import TypeAlias

from dotenv import load_dotenv
from pydantic import BaseSettings

Seconds: TypeAlias = int

# Cors and other basic settings
ALLOWED_ORIGINS = "http://localhost:8000"
ALLOWED_METHODS = "*"
ALLOWED_HEADERS = "*"

# Directories
SRC_DIR = Path(__file__).resolve().parent.parent  # /src
BASE_DIR = SRC_DIR.parent

if bool(os.getenv("READ_FROM_FILE")) is True:
    load_dotenv(BASE_DIR / ".env")

# JWT
JWT_ACCESS_TOKEN_EXPIRE: Seconds = 60 * 30  # 30 minutes
JWT_REFRESH_TOKEN_EXPIRE: Seconds = 60 * 60 * 24 * 7  # 7 days
JWT_ALGORITHM = "HS256"

# staticfiles
STATIC_DOMAIN = "http://localhost:8000"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "media"

# Pagination
PAGE_SIZE_DEFAULT = 10

# Chat
CHAT_INVITE_LINK_DURATION: Seconds = 60 * 60 * 24  # 24 hours


class Settings(BaseSettings):
    """Settings for env variables."""

    secret_key: str
    database_url: str
    messaging_url: str


settings = Settings()
