# Application configuration
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application settings loaded from environment variables
    API_TITLE: str = "Image-to-Video Chatbot"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ])

    SVD_MODEL_ID: str = "stabilityai/stable-video-diffusion-img2vid-xt"
    SVD_DEVICE: str = "cuda"
    SVD_NUM_FRAMES: int = 25
    SVD_FPS: int = 7
    SVD_DECODE_CHUNK_SIZE: int = 8
    GENERATED_MEDIA_DIR: str = str(Path("backend/generated").resolve())
    PUBLIC_BASE_URL: str = "http://127.0.0.1:8000"

    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "o3-mini"

    DEFAULT_VIDEO_DURATION: int = 5
    MAX_VIDEO_DURATION: int = 10
    DEFAULT_VIDEO_PROVIDER: str = "svd"
    REQUEST_TIMEOUT: int = 300

    SECRET_KEY: str = "change-me-in-.env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/image_to_video_chatbot"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )


settings = Settings()
