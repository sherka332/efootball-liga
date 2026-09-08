from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str

    BOT_TOKEN: str

    ADMIN_TELEGRAM_IDS: str = "1342256845"

    WEBAPP_URL: str = ""

    TIMEZONE: str = "Asia/Tashkent"

    RESULT_DEADLINE_HOUR: int = 23

    RESULT_DEADLINE_MINUTE: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def admin_ids(self) -> set[int]:
        return {
            int(x.strip())
            for x in self.ADMIN_TELEGRAM_IDS.split(",")
            if x.strip()
        }


settings = Settings()
