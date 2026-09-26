from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="FUKIDASHI_", env_file=".env", extra="ignore")

    nebius_api_token: str = Field(default="", validation_alias="NEBIUS_API_TOKEN")
    base_url: str = "https://api.tokenfactory.nebius.com/v1"
    model: str = "moonshotai/Kimi-K3"
    lang: str = "English"
    max_tokens: int = 65536
    memory_chars: int = 16000
    volume_memory: bool = True
    stall_timeout: float = 60
    workers: int = 2
    attempts: int = 3
    step_timeout: float = 600
    data_dir: Path = Path("data")
    host: str = "127.0.0.1"
    port: int = 8083


settings = Settings()
