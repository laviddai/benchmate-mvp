# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from pathlib import Path
from typing import Optional

BACKEND_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    DATABASE_URL: str

    # --- MinIO/S3 Settings ---
    S3_ENDPOINT_URL: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET_NAME_DATASETS: str = "benchmate-datasets" # Default if not in .env
    S3_BUCKET_NAME_RESULTS: str = "benchmate-results"   # Default if not in .env
    S3_USE_SSL: bool = True # Default to True for S3, override in .env for MinIO
    S3_REGION_NAME: str = "us-east-1" # Default region

    # Example of other settings you might add later:
    # SECRET_KEY: str = "a_very_secret_key_that_should_be_long_and_random"
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
        
    REDIS_HOSTNAME: str = "redis"
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file= BACKEND_ROOT_DIR / ".env",
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = Settings()

# Verify S3 settings are loaded (for debugging, remove later)
# print(f"S3_ENDPOINT_URL: {settings.S3_ENDPOINT_URL}")
# print(f"S3_BUCKET_NAME_DATASETS: {settings.S3_BUCKET_NAME_DATASETS}")