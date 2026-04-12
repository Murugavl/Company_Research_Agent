import os
import asyncio
from typing import List, Dict, Tuple, Optional, Any
from functools import lru_cache

from groq import Groq
from models import AccountPlanModel as AccountPlan
from .tools import research_company, split_into_sections, complete_missing_sections
from config import settings
from .logger import logger

# Phase 2.3 & 3.3 Imports
from database.db import save_research, get_last_research
from database.differ import diff_plans

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


async def progressive_research_company(company_name: str) -> Dict[str, Any]:
    """Perform tiered research with parallel processing for speed."""
    logger.info(f"Starting progressive research for: {company_name}")
    
    # Tier 1: Initial Discovery
    base_data = await research_company(company_name)
    raw_text = base_data.get("raw_answer", "")
    
    # Tier 2: Parallel Analysis (CONCURENT)
    # Both tools work on the raw text to extract and verify info
    split_task = split_into_sections(raw_text, company_name)
    complete_task = complete_missing_sections(raw_text, company_name)
    
    sections_base, sections_enriched = await asyncio.gather(split_task, complete_task)
    
    # Merge strategy: Enriched overwrites empty or generic base values
    final_sections = sections_base.copy()
    for k, v in sections_enriched.items():
        if not final_sections.get(k) or len(str(final_sections.get(k))) < 20:
            final_sections[k] = v

    conflicts = []
    if "revenue" in raw_text.lower() and "$" not in raw_text:
        conflicts.append("Revenue information appears unclear")

    return {
        "raw": raw_text,
        "sections": final_sections,
        "conflicts": conflicts
    }


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
        session_id: str  # Phase 3.3
    ) -> Tuple[str, AccountPlan, List[Dict[str, str]], Dict[str, Any]]:
    """Main entry point for agent logic. Async for concurrent tool usage."""
    
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
            # If it's a new company, reset plan
            if candidate != company_name:
                current_plan = None
            company_name = candidate

    company_name = normalize_company_name(company_name)
    diff_result = {}

    if current_plan is None:
        logger.info(f"Generating new plan for {company_name}")
        
        # Phase 2.3: Get last research before saving new one
        last_research = get_last_research(company_name, session_id)
        
        research_data = await progressive_research_company(company_name)
        
        sections = research_data["sections"]
        plan = AccountPlan(
            company_name=company_name,
            overview=sections.get("overview", ""),
            products_services=sections.get("products_services", ""),
            market_position=sections.get("market_position", ""),
            competitors=sections.get("competitors", ""),
            financial_snapshot=sections.get("financial_snapshot", ""),
            key_contacts=sections.get("key_contacts", ""),
            opportunities=sections.get("opportunities", ""),
            risks=sections.get("risks", ""),
            recommended_actions=sections.get("recommended_actions", "")
        )
        
        # Phase 2.3: Save new research and calculate diff
        current_data = plan.model_dump()
        save_research(company_name, current_data, session_id)
        
        if last_research:
            diff_result = diff_plans(last_research, current_data)
            
    else:
        plan = current_plan

    plan_dict = plan.model_dump()
    history_lines = [
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in chat_history[-settings.MAX_CHAT_HISTORY:]
    ]
    history_text = "\n".join(history_lines)

    if target_section and wants_update:
        logger.info(f"Updating section: {target_section} for {company_name}")
        update_prompt = f"""
{SYSTEM_INSTRUCTIONS}
Rewrite ONLY the '{target_section}' section.
Company: {company_name}
Current text: {plan_dict.get(target_section)}
User request: {user_message}
Return ONLY the updated text.
"""
        new_text = call_groq(update_prompt).strip()
        setattr(plan, target_section, new_text)
        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"
    else:
        prompt = f"""
{SYSTEM_INSTRUCTIONS}
Company: {company_name}
Structured info: {plan_dict}
Recent conversation: {history_text}
User message: {user_message}
Answer naturally and directly.
"""
        reply = call_groq(prompt)

    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return reply, plan, new_history, diff_result
