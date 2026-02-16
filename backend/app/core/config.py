from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///bossy_radar.db"
    ARCHIVE_DATABASE_URL: str = "sqlite:///archive.db"
    MOENV_API_KEY: str = ""
    BACKEND_CORS_ORIGINS: list[str] = []

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
