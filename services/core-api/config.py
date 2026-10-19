from pydantic_settings import BaseSettings, SettingsConfigDict


class CoreSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    HOST: str = "0.0.0.0"
    CORE_API_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://homelab:homelab_secret_pass@postgres:5432/homelab_db"
    AGENT_URL: str = "http://agent:8001"


settings = CoreSettings()
