from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    BOT_TOKEN: str
    ADMIN_ID: str = "@Red_buII"
    ADMIN_TG_ID: Optional[str] = None
    CORE_API_URL: str = "http://core-api:8000"

    @property
    def admin_identifier(self) -> str:
        return self.ADMIN_TG_ID if self.ADMIN_TG_ID else self.ADMIN_ID


settings = BotSettings()
