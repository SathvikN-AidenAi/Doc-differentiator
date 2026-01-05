import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://docdiff_user:docdiff_password@localhost:5432/docdiff_db"
    )

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_API_VERSION: str = os.getenv("AZURE_OPENAI_API_VERSION", "2025-03-01-preview")
    AZURE_OPENAI_DEPLOYMENT: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "o4-mini")

    # File Storage
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "uploads"
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "50"))

    # Session
    SESSION_TIMEOUT_HOURS: int = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))

    class Config:
        env_file = ".env"

settings = Settings()

# Create upload directory if it doesn't exist
settings.UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
