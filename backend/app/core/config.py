# backend/app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    """
    Application settings.

    Pydantic-settings will automatically attempt to load values for these
    fields from environment variables. If an environment variable is not set,
    it will try to load from a .env file if model_config.env_file is specified.
    """

    DATABASE_URL: str

    # Example of other settings you might add later:
    # SECRET_KEY: str = "a_very_secret_key_that_should_be_long_and_random" # For JWT
    # ALGORITHM: str = "HS256" # For JWT
    # ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 # e.g., 24 hours

    # SMTP settings for email (if you add email functionality)
    # SMTP_TLS: bool = True
    # SMTP_PORT: int | None = None
    # SMTP_HOST: str | None = None
    # SMTP_USER: str | None = None
    # SMTP_PASSWORD: str | None = None
    # EMAILS_FROM_EMAIL: str | None = None # Sender email address
    # EMAILS_FROM_NAME: str | None = None # Sender name

    # Configure Pydantic-settings behavior
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"),
        env_file_encoding='utf-8',
        extra='ignore' # Ignore extra fields in .env file
    )
    # The os.path.join(...) constructs the path to backend/.env from backend/app/core/config.py

# Create a single instance of the settings to be imported elsewhere
settings = Settings()

# You can print to verify during startup if needed, then remove
# print(f"Loading settings from: {settings.model_config.get('env_file')}")
# print(f"DATABASE_URL loaded: {'*' * (len(settings.DATABASE_URL) - 5) + settings.DATABASE_URL[-5:] if settings.DATABASE_URL else None}")