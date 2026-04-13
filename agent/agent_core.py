import os
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from functools import lru_cache

from groq import Groq
from models import AccountPlanModel as AccountPlan
from config import settings
from .logger import logger

# LangGraph Imports
from .graph import research_graph

groq_client = Groq(api_key=settings.GROQ_API_KEY)
MODEL_NAME = settings.GROQ_MODEL_NAME

SYSTEM_INSTRUCTIONS = """
You are a company research assistant.
Rules:
- Answer naturally and professionally. Do not mention any 'account plan' or internal sections.
- Use a short 1–2 line intro, then markdown bullet points where helpful.
- When the user asks to update a specific section, rewrite only that section and return just the updated text.
- When the user asks general questions, answer directly using research and reasonable inference.
- Keep the tone concise, clear, and business-focused.
- Never reuse any text from earlier answers.
- Never bring in content from previously discussed companies.
- Only talk about the company currently mentioned by the user.
- Ignore chat history unless the user is continuing the same company discussion.
"""

SECTION_KEYWORDS: Dict[str, List[str]] = {
    "overview": ["overview", "summary", "about the company", "intro"],
    "products_services": ["product", "service", "offerings", "solutions"],
    "market_position": ["market", "position", "segment"],
    "competitors": ["competitor", "competition"],
    "financial_snapshot": ["financial", "revenue", "profit"],
    "key_contacts": ["contact", "stakeholder"],
    "opportunities": ["opportunity", "growth"],
    "risks": ["risk", "challenge"],
    "recommended_actions": ["recommendation", "action"],
}

UPDATE_KEYWORDS = ["update", "change", "edit", "modify", "rewrite", "revise"]

def detect_target_section(user_message: str) -> Optional[str]:
    msg = user_message.lower()
    for section, words in SECTION_KEYWORDS.items():
        for w in words:
            if w in msg:
                return section
    return None

def is_update_intent(user_message: str) -> bool:
    msg = user_message.lower()
    return any(w in msg for w in UPDATE_KEYWORDS)

def call_groq(prompt: str) -> str:
    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        return response.choices[0].message.content.strip() if response.choices else ""
    except Exception as e:
        logger.error(f"Groq API call failed: {e}")
        return ""

@lru_cache(maxsize=100)
def normalize_company_name(raw_name: str) -> str:
    raw_name = (raw_name or "").strip()
    if not raw_name:
        return raw_name
    try:
        prompt = (
            "Correct this company name to its proper official capitalization. "
            "Return only the corrected name.\n\n"
            f"Name: {raw_name}"
        )
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=50
        )
        name = response.choices[0].message.content.strip() if response.choices else ""
        if name:
            return name
    except Exception:
        pass
    return " ".join(word.capitalize() for word in raw_name.split())

def get_last_company_from_history(chat_history: List[Dict[str, str]]) -> Optional[str]:
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            possible = normalize_company_name(msg["content"])
            if possible and len(possible.split()) <= 3:
                banned = {"can", "you", "tell", "update", "its", "about", "the"}
                if not any(w in banned for w in possible.lower().split()):
                    return possible
    return None

async def generate_agent_reply(
        user_message: str,
        company_name: str,
        current_plan: Optional[AccountPlan],
        chat_history: List[Dict[str, str]],
        session_id: str
    ) -> Tuple[str, AccountPlan, List[Dict[str, str]], Dict[str, Any]]:
    """
    Main entry point for agent logic. 
    Uses LangGraph for the research orchestration.
    """
    
    target_section = detect_target_section(user_message)
    wants_update = is_update_intent(user_message)

    if wants_update:
        last_company = get_last_company_from_history(chat_history)
        if last_company:
            company_name = last_company
    else:
        candidate = normalize_company_name(user_message)
        banned = {"can", "you", "tell", "about", "update", "its", "the", "edit"}
        if candidate and not any(w in banned for w in candidate.lower().split()):
            if candidate != company_name:
                current_plan = None
            company_name = candidate

    company_name = normalize_company_name(company_name)

    # Specific section update request on an existing plan
    if current_plan and target_section and wants_update:
        logger.info(f"Rapid update for section: {target_section} - {company_name}")
        plan_dict = current_plan.model_dump()
        update_prompt = f"""
{SYSTEM_INSTRUCTIONS}
Rewrite ONLY the '{target_section}' section.
Company: {company_name}
Current text: {plan_dict.get(target_section)}
User request: {user_message}
Return ONLY the updated text.
"""
        new_text = call_groq(update_prompt).strip()
        setattr(current_plan, target_section, new_text)
        
        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"
        new_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        return reply, current_plan, new_history, {}

    # Otherwise, perform research using LangGraph
    logger.info(f"Invoking research graph for {company_name}")
    
    initial_state = {
        "user_message": user_message,
        "company_name": company_name,
        "session_id": session_id,
        "chat_history": chat_history,
        "current_plan": current_plan.model_dump() if current_plan else None,
        "raw_research": "",
        "sections_base": {},
        "sections_enriched": {},
        "final_sections": {},
        "reply": "",
        "diff_result": {},
        "conflicts": [],
        "error": None
    }
    
    try:
        # Run the graph
        result = await research_graph.ainvoke(initial_state)
        
        # Extract results from state
        final_sections = result.get("final_sections", {})
        plan = AccountPlan(
            company_name=result.get("company_name", company_name),
            overview=final_sections.get("overview", ""),
            products_services=final_sections.get("products_services", ""),
            market_position=final_sections.get("market_position", ""),
            competitors=final_sections.get("competitors", ""),
            financial_snapshot=final_sections.get("financial_snapshot", ""),
            key_contacts=final_sections.get("key_contacts", ""),
            opportunities=final_sections.get("opportunities", ""),
            risks=final_sections.get("risks", ""),
            recommended_actions=final_sections.get("recommended_actions", "")
        )
        
        reply = result.get("reply", "I have completed the research.")
        diff_result = result.get("diff_result", {})
        
        new_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        
        return reply, plan, new_history, diff_result
        
    except Exception as e:
        logger.error(f"Graph execution failed: {e}", exc_info=True)
        # Fallback to a simple error reply
        error_reply = "I encountered an error during research. Please try again."
        return error_reply, current_plan or AccountPlan(company_name=company_name), chat_history, {}
