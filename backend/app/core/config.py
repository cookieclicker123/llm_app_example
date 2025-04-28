from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pathlib import Path # Import Path
from pydantic import PostgresDsn, RedisDsn # Import validation types
from dotenv import load_dotenv # Import load_dotenv

# Explicitly load .env file from the project root
# This helps when config.py is imported from scripts running in different directories (like Alembic)
DOTENV_PATH = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=DOTENV_PATH)

class Settings(BaseSettings):
    """Application settings managed by Pydantic BaseSettings.

    Settings are loaded in the following priority:
    1. Environment variables (case-insensitive).
    2. Values from a .env file (if present).
    3. Default values defined in this class.
    """

    # Application settings
    APP_NAME: str = "End-to-End LLM App"
    API_V1_STR: str = "/api/v1"
    LOG_LEVEL: str = "INFO"

    # Ollama specific settings
    OLLAMA_BASE_URL: str = "http://localhost:11434" # Default for local Ollama
    OLLAMA_DEFAULT_MODEL: str = "gemma3:12b-it-qat" # Example default model
    OLLAMA_REQUEST_TIMEOUT: int = 60 # Timeout in seconds

    # Directory for saving chat responses (relative to project root assumed by default usage)
    CHAT_RESPONSE_SAVE_DIR: Path = Path("backend/tmp/json_sessions")

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0 # Default Redis DB

    # Database Settings
    DATABASE_URL: PostgresDsn
    # Example: postgresql+asyncpg://appuser:your_secure_password@postgres:5432/appdb
    DB_ECHO_LOG: bool = False # Set to True in .env for development SQL logging

    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Redis URL (derived or explicitly set)
    # If REDIS_PASSWORD is set in .env, it should be included here if constructing manually
    # Alternatively, let docker-compose handle the password for the service connection
    REDIS_URL: RedisDsn

    # Add other settings like Database URL, Redis URL, etc., later
    # DATABASE_URL: str = "postgresql://user:password@host:port/db"
    # REDIS_URL: str = "redis://localhost:6379"

    # Configure Pydantic BaseSettings - it will now pick up pre-loaded env vars
    model_config = SettingsConfigDict(extra='ignore') # No need for env_file here anymore

# Use lru_cache to create a singleton instance of the Settings class.
# This ensures that the settings are loaded only once.
@lru_cache
def get_settings() -> Settings:
    """Returns the cached Settings instance."""
    return Settings()

# Expose a single settings instance for easy import
settings = get_settings() 