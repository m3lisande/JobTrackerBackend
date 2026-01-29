from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://melisande@localhost:5432/jobtracker"
    track_modifications: bool = False

    class Config:
        env_prefix = ""
        env_file = ".env"
        fields = {
            "database_url": {"env": ["DATABASE_URL"]},
            "track_modifications": {"env": ["TRACK_MODIFICATIONS"]}
        }


settings = Settings()