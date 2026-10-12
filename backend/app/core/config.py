from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Imperial Restaurant OS"
    ENVIRONMENT: str = "dev"

    DATABASE_URL: str = "postgresql+asyncpg://imperial:change_me@localhost:5432/imperial"
    REDIS_URL: str = "redis://localhost:6379/0"

    JWT_SECRET: str = "replace_with_strong_secret_at_least_256_bits_for_imperial_restaurant"
    JWT_ALGORITHM: str = "HS256"
    JWT_ISSUER: str = "imperial-restaurant-os"
    JWT_AUDIENCE: str = "imperial-api"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    LOGIN_MAX_FAILURES: int = 5
    LOGIN_BLOCK_MINUTES: int = 15

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]

    SEED_ADMIN_EMAIL: str = "admin@imperial.local"
    SEED_ADMIN_PASSWORD: str = "ChangeMe123!"

    QR_BASE_URL: str = "http://localhost:3000/mesa"
    INVENTORY_ALLOW_NEGATIVE_STOCK: bool = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            val = value.strip()
            if val.startswith("[") and val.endswith("]"):
                import json
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        return value

    @field_validator("QR_BASE_URL")
    @classmethod
    def normalize_qr_base_url(cls, value: str) -> str:
        return value.rstrip("/")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
