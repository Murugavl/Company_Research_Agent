from typing import List, Dict, Tuple, Optional, TypedDict

class AgentState(TypedDict):
    """
    Represents the state of the research agent during graph execution.
    """
    user_message: str
    company_name: str
    session_id: str
    chat_history: List[Dict[str, str]]
    current_plan: Optional[Dict]
    raw_research: str
    sections_base: Dict
    sections_enriched: Dict
    final_sections: Dict
    reply: str
    diff_result: Dict
    conflicts: List[str]
    error: Optional[str]
