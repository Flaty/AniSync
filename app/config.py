from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://anime:anime@localhost:5432/anisync"
    redis_url: str = "redis://localhost:6379"

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='forbid'
    )

settings = Settings()

