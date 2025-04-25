from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

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
    OLLAMA_DEFAULT_MODEL: str = "deepseek-r1:14b" # Example default model
    OLLAMA_REQUEST_TIMEOUT: int = 60 # Timeout in seconds

    # Add other settings like Database URL, Redis URL, etc., later
    # DATABASE_URL: str = "postgresql://user:password@host:port/db"
    # REDIS_URL: str = "redis://localhost:6379"

    # Configure Pydantic BaseSettings to load from a .env file
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

# Use lru_cache to create a singleton instance of the Settings class.
# This ensures that the settings are loaded only once.
@lru_cache
def get_settings() -> Settings:
    """Returns the cached Settings instance."""
    return Settings()

# Expose a single settings instance for easy import
settings = get_settings() 