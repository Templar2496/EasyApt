from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="backend/.env",
        extra="ignore",  # ignore stray/old keys
    )
    APP_NAME: str = "EasyAPT"
    DB_URL: str
    JWT_SECRET: str
    JWT_TTL_SECONDS: int = 900
    LOCKOUT_THRESHOLD: int = 5
    LOCKOUT_MINUTES: int = 15


settings = Settings()
