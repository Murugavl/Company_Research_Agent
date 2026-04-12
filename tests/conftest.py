import pytest
import sqlite3
import os
from unittest.mock import MagicMock, AsyncMock
from pydantic import BaseModel

# Mock Pydantic model for tools testing
class MockModel(BaseModel):
    name: str
    value: int

@pytest.fixture
def mock_groq_client():
    """Fixture to mock Groq completions."""
    mock = MagicMock()
    mock.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content='{"overview": "mocked overview"}'))]
    )
    return mock

@pytest.fixture
def mock_tavily_response():
    """Sample Tavily payload."""
    return {
        "answer": "Microsoft is a technology company.",
        "results": [{"title": "MSFT Info", "url": "https://msft.com"}]
    }

@pytest.fixture
def temp_db():
    """Creates a fresh in-memory SQLite db for each test."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Initialize schema
    conn.execute("""
        CREATE TABLE research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            company TEXT NOT NULL,
            researched_at TEXT NOT NULL,
            overview TEXT,
            products_services TEXT,
            market_position TEXT,
            competitors TEXT,
            financial_snapshot TEXT,
            key_contacts TEXT,
            opportunities TEXT,
            risks TEXT,
            recommended_actions TEXT
        )
    """)
    yield conn
    conn.close()
