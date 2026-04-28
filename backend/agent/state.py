from typing import List, Dict, Optional, TypedDict, Any

class AgentState(TypedDict):
    """
    Represents the state of the research agent during graph execution.
    """
    user_message: str
    company_name: str
    session_id: str
    chat_history: List[Dict[str, str]]
    current_plan: Optional[Dict[str, Any]]
    raw_research: str
    images: List[str]
    sections_base: Dict[str, Any]
    sections_enriched: Dict[str, Any]
    final_sections: Dict[str, Any]
    reply: str
    diff_result: Dict[str, Any]
    conflicts: List[str]
    error: Optional[str]
