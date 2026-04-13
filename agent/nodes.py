import asyncio
from typing import Dict, Any, List
from .state import AgentState
from .tools import research_company, split_into_sections, complete_missing_sections
from database.db import get_last_research, save_research
from database.differ import diff_plans
from config import settings

async def node_normalize(state: AgentState) -> Dict:
    """Normalize the company name to its official version."""
    from .agent_core import normalize_company_name
    normalized = normalize_company_name(state["company_name"])
    return {"company_name": normalized}

async def node_research(state: AgentState) -> Dict:
    """Perform initial web research using Tavily."""
    res = await research_company(state["company_name"])
    return {"raw_research": res.get("raw_answer", "")}

async def node_split(state: AgentState) -> Dict:
    """Analyze raw research and split into structured sections."""
    res = await split_into_sections(state["raw_research"], state["company_name"])
    return {"sections_base": res}

async def node_complete(state: AgentState) -> Dict:
    """Enrich sections with strategic inference and missing context."""
    res = await complete_missing_sections(state["raw_research"], state["company_name"])
    return {"sections_enriched": res}

async def node_merge(state: AgentState) -> Dict:
    """Merge base and enriched sections based on quality and length."""
    sb = state.get("sections_base", {})
    se = state.get("sections_enriched", {})
    
    merged = sb.copy()
    for k, v in se.items():
        if not merged.get(k) or len(str(merged.get(k))) < 20:
            merged[k] = v
            
    return {"final_sections": merged}

async def node_reply(state: AgentState) -> Dict[str, Any]:
    """Generate the final natural language reply for the user."""
    from .agent_core import call_groq, SYSTEM_INSTRUCTIONS
    
    plan_dict = state["final_sections"]
    history = state["chat_history"]
    
    history_lines = [
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in history[-settings.MAX_CHAT_HISTORY:]
    ]
    history_text = "\n".join(history_lines)
    
    prompt = f"""
{SYSTEM_INSTRUCTIONS}
Company: {state['company_name']}
Structured info: {plan_dict}
Recent conversation: {history_text}
User message: {state['user_message']}
Answer naturally and directly.
"""
    reply_text = call_groq(prompt)
    return {"reply": reply_text}

async def node_save(state: AgentState) -> Dict:
    """Save the research result to the database and calculate diff from previous version."""
    company_name = state["company_name"]
    session_id = state["session_id"]
    current_data = state["final_sections"].copy()
    current_data["company_name"] = company_name
    
    last_research = get_last_research(company_name, session_id)
    save_research(company_name, current_data, session_id)
    
    diff = {}
    if last_research:
        diff = diff_plans(last_research, current_data)
        
    return {"diff_result": diff}
