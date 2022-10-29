from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    """

    jwt_key: str

    class Config:
        env_file = ".env"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns the (cached) application settings object.

    FastAPI dependency.
    """
    return Settings()  # type: ignore
