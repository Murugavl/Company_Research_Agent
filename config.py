from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Configuration (Required)
    GROQ_API_KEY: str = Field(..., description="API key for Groq")
    TAVILY_API_KEY: str = Field(..., description="API key for Tavily Search")

    # Model Settings
    GROQ_MODEL_NAME: str = Field(default="llama-3.3-70b-versatile")

    # Search Settings
    TAVILY_MAX_RESULTS: int = Field(default=5)

    # Chat Settings
    MAX_CHAT_HISTORY: int = Field(default=6)

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    # LangSmith Tracing
    LANGCHAIN_API_KEY: Optional[str] = Field(default=None)
    LANGCHAIN_TRACING_V2: str = Field(default="false")
    LANGCHAIN_PROJECT: str = Field(default="company-research-agent")

# Initialize settings
try:
    settings = Settings()
except Exception as e:
    import sys
    print(f"⚠️  Configuration Error: {e}")
    sys.exit(1)
