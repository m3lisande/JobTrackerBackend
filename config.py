from pathlib import Path

from pydantic_settings import BaseSettings

# Resolve .env relative to this file so it's found regardless of cwd
_env_file = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    database_url: str
    track_modifications: bool = False

    # Backblaze B2 (S3-compatible) - optional; omit to disable resume uploads
    b2_key_id: str | None = None
    b2_app_key: str | None = None
    b2_bucket_name: str | None = None
    b2_endpoint: str | None = None  # e.g. https://s3.us-west-004.backblazeb2.com
    b2_region: str = "us-west-004"   # region in endpoint, used for signing

    class Config:
        env_prefix = ""
        env_file = str(_env_file)
        env_file_encoding = "utf-8"
        extra = "ignore"
        fields = {
            "database_url": {"env": ["DATABASE_URL"]},
            "track_modifications": {"env": ["TRACK_MODIFICATIONS"]},
            "b2_key_id": {"env": ["B2_KEY_ID"]},
            "b2_app_key": {"env": ["B2_APP_KEY"]},
            "b2_bucket_name": {"env": ["B2_BUCKET_NAME"]},
            "b2_endpoint": {"env": ["B2_ENDPOINT"]},
            "b2_region": {"env": ["B2_REGION"]},
        }

    @property
    def b2_configured(self) -> bool:
        return bool(
            self.b2_key_id and self.b2_app_key
            and self.b2_bucket_name and self.b2_endpoint
        )


settings = Settings()