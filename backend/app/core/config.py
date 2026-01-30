from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///bossy_radar.db"
    ARCHIVE_DATABASE_URL: str = "sqlite:///archive.db"
    BACKEND_CORS_ORIGINS: list[str] = []


    class Config:
        env_file = ".env"

settings = Settings()
