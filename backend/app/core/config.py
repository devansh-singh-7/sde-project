from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Q&A App"
    SECRET_KEY: str = "change-me-in-production" # Change in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "mongodb://admin:changeme@mongo:27017/ai_qa_db?authSource=admin"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # External APIs and Storage
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_PROJECT_NAME: Optional[str] = None
    GEMINI_PROJECT_NUMBER: Optional[str] = None

    # Optional fallback for legacy OpenAI transcription path
    OPENAI_API_KEY: str = ""
    AWS_BUCKET_NAME: Optional[str] = None
    
    # File Upload Settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 500

    model_config = SettingsConfigDict(env_file=(".env", "../.env"), case_sensitive=True, extra="ignore")

settings = Settings()
