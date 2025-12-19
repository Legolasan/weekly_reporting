from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "Work Tracker"
    debug: bool = True
    database_url: str = "postgresql://localhost/work_tracker"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
