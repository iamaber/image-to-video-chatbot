# Application configuration
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application settings loaded from environment variables
    
    # API Configuration
    API_TITLE: str = "Image-to-Video Chatbot"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # Video Generation Providers
    RUNWAY_API_KEY: Optional[str] = None
    MINIMAX_API_KEY: Optional[str] = None
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "o3-mini"
    
    # Default settings
    DEFAULT_VIDEO_DURATION: int = 5
    MAX_VIDEO_DURATION: int = 10
    DEFAULT_VIDEO_PROVIDER: str = "runway"
    
    # Request timeout
    REQUEST_TIMEOUT: int = 300
    
    # JWT Authentication
    SECRET_KEY: str = "123"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 24
    
    # PostgreSQL Database Configuration (Neon DB)
    DATABASE_URL: str = "postgresql://neondb_owner:npg_RGxFdX1e8hIY@ep-old-field-a1x9vux0-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
