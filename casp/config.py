from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    elevenlabs_api_key: str = ""
    default_model: str = "claude-opus-4-6"
    max_iterations: int = 3
    output_dir: Path = Path("./output")
    # When True, LLM calls are intercepted and served from fixtures (CI/test mode)
    test_mode: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )


# Singleton — imported everywhere as `from casp.config import settings`
settings = Settings()
