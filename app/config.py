from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "ComicCraft"
    APP_ENV: str = "development"
    DEBUG: bool = True

    GEMINI_API_KEY: str = ""
    GEMINI_OUTLINE_MODEL: str = "gemini-3.8-flash"
    GEMINI_STORY_MODEL: str = "gemini-3.8-flash"

    IMAGE_PROVIDER: str = "placeholder"

    HF_API_KEY: str = ""
    HF_IMAGE_MODEL: str = "stabilityai/stable-diffusion-xl-base-1.0"
    LOCAL_IMAGE_MODEL: str = "runwayml/stable-diffusion-v1-5"

    IMAGE_WIDTH: int = 768
    IMAGE_HEIGHT: int = 768
    IMAGE_STEPS: int = 25
    IMAGE_GUIDANCE: float = 7.5

    MAX_PANELS: int = 5
    MAX_PROMPT_LENGTH: int = 1200

    BASE_DIR: Path = BASE_DIR
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    STATIC_DIR: Path = BASE_DIR / "static"
    PANELS_DIR: Path = BASE_DIR / "static" / "panels"
    EXPORTS_DIR: Path = BASE_DIR / "static" / "exports"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

settings.PANELS_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)