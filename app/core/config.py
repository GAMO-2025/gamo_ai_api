from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    GEMINI_API_KEY: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DEBUG: bool = False
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()