import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/efootball.db"
    secret_key: str = "change-this"
    cors_origins: str = "http://localhost:5173,http://localhost:5174"
    telegram_bot_token: str = ""
    telegram_admin_id: str = ""
    seed_admin: bool = True
    admin_username: str = "admin"
    admin_password: str = "admin123"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_list(self):
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
