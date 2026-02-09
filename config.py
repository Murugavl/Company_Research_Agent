"""
Configuration settings for Company Research Agent
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Model Settings
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-2.0-flash")

# Search Settings
TAVILY_MAX_RESULTS = int(os.getenv("TAVILY_MAX_RESULTS", "5"))

# Chat Settings
MAX_CHAT_HISTORY = int(os.getenv("MAX_CHAT_HISTORY", "6"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Validate required API keys
def validate_config():
    """Validate that required configuration is present"""
    errors = []

    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set in environment variables")

    if not TAVILY_API_KEY:
        errors.append("TAVILY_API_KEY is not set in environment variables")

    if errors:
        raise ValueError(
            "Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors)
        )

# Run validation on import
try:
    validate_config()
except ValueError as e:
    print(f"⚠️  Configuration Error: {e}")
    print("Please create a .env file with required API keys (see .env.example)")

