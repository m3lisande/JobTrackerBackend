from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env relative to this file so it's found regardless of cwd
_env_file = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    database_url: str
    track_modifications: bool = False

    class Config:
        env_prefix = ""
        env_file = str(_env_file)
        env_file_encoding = "utf-8"
        extra = "ignore"
        fields = {
            "database_url": {"env": ["DATABASE_URL"]},
            "track_modifications": {"env": ["TRACK_MODIFICATIONS"]},
        }


settings = Settings()