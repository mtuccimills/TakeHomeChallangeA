import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_ENV = os.getenv("APP_ENV", "development")
_env_file = ".env.test" if APP_ENV == "test" else ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_env_file, env_file_encoding="utf-8", extra="ignore"
    )

    secret_key: SecretStr
    external_api_url: str

    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    database_url: str

    max_child_per_page: int = 10


settings = Settings()  # Loaded from .env or .env.test depending on APP_ENV
