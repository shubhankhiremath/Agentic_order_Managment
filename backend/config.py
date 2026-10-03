from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    database_url: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'olist.db').as_posix()}"
    chroma_path: str = str(PROJECT_ROOT / "data" / "chroma")
    dataset_dir: str = str(PROJECT_ROOT / "dataset")
    knowledge_base_dir: str = str(PROJECT_ROOT / "knowledge_base")
    # Historical dataset "today" for open-order exception rules (demo only).
    dataset_as_of_date: str = "2018-10-17"
    long_delivery_days: int = 30
    agent_recursion_limit: int = 12
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
