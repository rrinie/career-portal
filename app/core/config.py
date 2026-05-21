"""
core/config.py
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    model_config = {
        # Path relative to WHERE you run uvicorn (project root)
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()