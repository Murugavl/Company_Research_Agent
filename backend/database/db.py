import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

DB_PATH = "research_history.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the research_history table with session isolation."""
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS research_history (
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
        conn.commit()

def save_research(company: str, plan: Dict[str, Any], session_id: str) -> None:
    """Save a research result linked to a specific session."""
    init_db()  # Ensure table exists
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO research_history (
                session_id, company, researched_at, 
                overview, products_services, market_position, 
                competitors, financial_snapshot, key_contacts, 
                opportunities, risks, recommended_actions
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            company,
            datetime.now().isoformat(),
            plan.get("overview"),
            plan.get("products_services"),
            plan.get("market_position"),
            plan.get("competitors"),
            plan.get("financial_snapshot"),
            plan.get("key_contacts"),
            plan.get("opportunities"),
            plan.get("risks"),
            plan.get("recommended_actions")
        ))
        conn.commit()

def get_last_research(company: str, session_id: str) -> Optional[Dict[str, Any]]:
    """Get the most recent research result for a company within a session."""
    init_db()
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM research_history 
            WHERE company = ? AND session_id = ?
            ORDER BY researched_at DESC LIMIT 1
        """, (company, session_id)).fetchone()
        
        if row:
            return dict(row)
    return None

def get_research_history(company: str, session_id: str) -> List[Dict[str, Any]]:
    """Get all past research results for a company within a session."""
    init_db()
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM research_history 
            WHERE company = ? AND session_id = ?
            ORDER BY researched_at DESC
        """, (company, session_id)).fetchall()
        
        return [dict(row) for row in rows]
