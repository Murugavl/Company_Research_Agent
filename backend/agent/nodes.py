import asyncio
from typing import Dict, Any, List, Optional
from .state import AgentState
from .tools import research_company, split_into_sections, complete_missing_sections
from config import settings

def diff_plans(old_plan, new_plan):
    diff = {}
    for key, new_val in new_plan.items():
        if key in ["company_name", "session_id", "researched_at", "id", "company_images"]:
            continue
        old_val = old_plan.get(key, "")
        if str(old_val).strip() != str(new_val).strip():
            diff[key] = {"old": str(old_val).strip(), "new": str(new_val).strip()}
    return diff

async def node_normalize(state: AgentState) -> Dict:
    """Normalize the company name to its official version."""
    from .agent_core import normalize_company_name
    normalized = normalize_company_name(state["company_name"])
    return {"company_name": normalized}

async def node_research(state: AgentState) -> Dict:
    """Perform initial web research using Tavily."""
    company_name = state["company_name"]
    
    # Run main research and dedicated image search concurrently
    research_task = asyncio.create_task(research_company(company_name))
    image_search_query = f"{company_name} company logo headquarters office buildings representative images"
    from .tools import tavily_search
    image_task = asyncio.create_task(tavily_search(image_search_query))
    
    res, img_data = await asyncio.gather(research_task, image_task)
    
    # Aggregate answer and snippets from results for better context
    answer = res.get("raw_answer", "")
    snippets = "\n".join([f"- {r.get('content', '')}" for r in res.get("sources", [])])
    
    # Combine images from both searches
    images = res.get("images", [])
    if img_data and img_data.get("images"):
        # Use a dict to avoid duplicates and limit to 10 images
        unique_images = list(dict.fromkeys(images + img_data.get("images", [])))
        images = unique_images[:10]
    
    combined = f"{answer}\n\nRELEVANT SNIPPETS:\n{snippets}"
    return {"raw_research": combined.strip(), "images": images}

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
        # Enriched overwrites short/empty base values < 20 chars
        if not merged.get(k) or len(str(merged.get(k))) < 20:
            merged[k] = v
            
    # Include images from state if present
    merged["company_images"] = state.get("images", [])
            
    return {"final_sections": merged}

async def node_reply(state: AgentState) -> Dict[str, Any]:
    """Generate the final natural language reply for the user."""
    from .agent_core import call_groq, SYSTEM_INSTRUCTIONS
    
    plan_dict = state["final_sections"]
    history = state["chat_history"]
    
    prompt = f"""
{SYSTEM_INSTRUCTIONS}
Company: {state['company_name']}
Structured info: {plan_dict}
Chat History: {history}
User message: {state['user_message']}

Answer naturally and professionally based on the research.
"""
    reply_text = call_groq(prompt)
    return {"reply": reply_text}

async def node_save(state: AgentState) -> Dict:
    """Calculate diff from previous version."""
    company_name = state["company_name"]
    current_data = state["final_sections"].copy()
    current_data["company_name"] = company_name
    
    last_research = state.get("current_plan")
    
    diff = {}
    if last_research:
        diff = diff_plans(last_research, current_data)
        
    return {"diff_result": diff}
