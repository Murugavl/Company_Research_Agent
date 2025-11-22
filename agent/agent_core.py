import os
from typing import List, Dict, Any, Tuple, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .account_plan import AccountPlan
from .tools import research_company, split_into_sections, complete_missing_sections

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"

# high-level behavior for the model
SYSTEM_INSTRUCTIONS = """
You are a company research assistant.

Rules:
- Answer naturally, do not mention any 'account plan' or internal sections.
- Use a short 1–2 line intro, then markdown bullet points where helpful.
- When the user asks to update a specific section (risks, opportunities, competitors, etc.),
  rewrite only that section and return just the updated text.
- When the user asks general questions (culture, location, work style, etc.),
  answer directly using research and reasonable inference.
- Keep the tone concise and business-focused.
"""

SECTION_KEYWORDS = {
    "overview": ["overview", "summary", "about the company", "intro"],
    "products_services": ["product", "service", "offerings", "solutions"],
    "market_position": ["market", "position", "branding", "segment"],
    "competitors": ["competitor", "competition", "rival"],
    "financial_snapshot": ["financial", "revenue", "profit", "loss", "funding"],
    "key_contacts": ["contact", "person", "stakeholder", "decision maker"],
    "opportunities": ["opportunity", "growth", "expansion", "upside"],
    "risks": ["risk", "challenge", "threat", "downside"],
    "recommended_actions": ["recommendation", "action", "next step", "plan"],
}

UPDATE_KEYWORDS = ["update", "change", "edit", "modify", "rewrite", "revise"]


# detect which section user is talking about
def detect_target_section(user_message: str) -> Optional[str]:
    lower_msg = user_message.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_msg:
                return section
    return None


# detect if user wants to update / rewrite something
def is_update_intent(user_message: str) -> bool:
    lower_msg = user_message.lower()
    return any(word in lower_msg for word in UPDATE_KEYWORDS)


# generic gemini call
def call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text.strip() if response.text else ""


# main agent function
def generate_agent_reply(
    user_message: str,
    company_name: str,
    current_plan: Optional[AccountPlan],
    chat_history: List[Dict[str, str]],
) -> Tuple[str, AccountPlan, List[Dict[str, str]]]:

    # build initial plan if not yet present
    if current_plan is None:
        plan = AccountPlan.empty(company_name)
        research = research_company(company_name)
        raw_text = research.get("raw_answer", "")

        sections = split_into_sections(raw_text)
        sections = complete_missing_sections(sections)

        plan.overview = sections.get("overview", "")
        plan.products_services = sections.get("products_services", "")
        plan.market_position = sections.get("market_position", "")
        plan.competitors = sections.get("competitors", "")
        plan.financial_snapshot = sections.get("financial_snapshot", "")
        plan.key_contacts = sections.get("key_contacts", "")
        plan.opportunities = sections.get("opportunities", "")
        plan.risks = sections.get("risks", "")
        plan.recommended_actions = sections.get("recommended_actions", "")
    else:
        plan = current_plan

    plan_dict = plan.to_dict()

    target_section = detect_target_section(user_message)
    wants_update = is_update_intent(user_message)

    # pack short history
    history_text_parts = []
    for msg in chat_history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text_parts.append(f"{role.upper()}: {content}")
    history_text = "\n".join(history_text_parts) if history_text_parts else ""

    # branch: section update vs normal answer
    if target_section and wants_update:
        # only rewrite that section and return it
        update_prompt = f"""
{SYSTEM_INSTRUCTIONS}

You are rewriting the '{target_section}' part for company: {company_name}.

Current text:
{plan_dict.get(target_section, "")}

User request:
{user_message}

Task:
- Rewrite only this section.
- Use a short 1–2 line intro, then markdown bullet points.
- Return ONLY the updated text for this section, nothing else.
"""
        new_section_text = call_gemini(update_prompt).strip()
        setattr(plan, target_section, new_section_text)

        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_section_text}"
    else:
        # normal question / general query
        prompt = f"""
{SYSTEM_INSTRUCTIONS}

Company: {company_name}

Structured info:
{plan_dict}

Recent conversation:
{history_text}

User message:
{user_message}

Answer the user directly. Do not mention any 'account plan' or internal structures.
Use a short intro, then bullet points where useful.
"""
        reply = call_gemini(prompt)

    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return reply, plan, new_history
