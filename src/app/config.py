from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    sqlalchemy_database_url: str
    paystack_secret_key: SecretStr
    paystack_url: str
    jwt_secret_key: str
    hashing_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_secret: str
    refresh_token_expire_days: int = 30
    mail_username: str
    mail_password: SecretStr


settings = Settings()
