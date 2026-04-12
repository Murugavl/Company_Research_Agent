import uuid
from fastapi import Header, HTTPException
from config import settings

def get_settings():
    """Dependency to provide application settings."""
    return settings

def validate_session_id(session_id: str):
    """Dependency to validate that session_id is a valid UUID string."""
    try:
        uuid.UUID(session_id)
        return session_id
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id format. Must be a UUID.")
