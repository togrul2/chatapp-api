import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(os.path.join(BASE_DIR, '.env'))
sys.path.append(str(BASE_DIR))

# JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
ALGORITHM = 'HS256'


class Settings(BaseSettings):
    """Settings for env variables."""
    secret_key: str
    postgres_db: str
    postgres_host: str
    postgres_port: str = 5432
    postgres_user: str
    postgres_password: str


settings = Settings()
