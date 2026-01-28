from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://melisande@localhost:5432/jobtracker"
    track_modifications: bool = False


settings = Settings()