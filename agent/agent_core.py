import os
from typing import List, Dict, Tuple, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .account_plan import AccountPlan
from .tools import research_company, split_into_sections, complete_missing_sections

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"

SYSTEM_INSTRUCTIONS = """
You are a company research assistant.

Rules:
- Answer naturally and professionally. Do not mention any 'account plan' or internal sections.
- Use a short 1–2 line intro, then markdown bullet points where helpful.
- When the user asks to update a specific section (risks, opportunities, competitors, etc.),
  rewrite only that section and return just the updated text.
- When the user asks general questions (culture, location, work style, etc.),
  answer directly using research and reasonable inference.
- Keep the tone concise, clear, and business-focused.
- When generating or updating the structured view, ALWAYS fill every section
  with meaningful, non-empty business content. Avoid very short or generic text.
"""

SECTION_KEYWORDS: Dict[str, List[str]] = {
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


def call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    res = model.generate_content(prompt)
    return res.text.strip() if res.text else ""


def normalize_company_name(raw_name: str) -> str:
    raw_name = (raw_name or "").strip()
    if not raw_name:
        return raw_name

    try:
        prompt = (
            "Correct this company name to its proper official capitalization and spacing. "
            "Return only the corrected name, no extra words.\n\n"
            f"Name: {raw_name}"
        )
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(prompt)
        name = (res.text or "").strip()
        if name:
            return name
    except Exception:
        pass

    # fallback – simple title-case
    return " ".join(word.capitalize() for word in raw_name.split())


def _fallback_text(section: str, company_name: str) -> str:
    c = company_name
    if section == "overview":
        return (
            f"{c} is a recognised player in its industry, providing core products and services, "
            f"serving a broad customer base, and focusing on innovation and operational efficiency."
        )
    if section == "products_services":
        return (
            f"{c} offers a portfolio of products and services that support its core customers. "
            f"These typically include primary offerings, supporting tools or platforms, and related "
            f"services such as consulting, support, or training."
        )
    if section == "market_position":
        return (
            f"{c} holds a competitive position in its market, with established brand recognition, "
            f"a measurable share in key segments, and a value proposition that differentiates it from "
            f"both traditional and emerging competitors."
        )
    if section == "competitors":
        return (
            "- Established companies offering similar products and services\n"
            "- Regional or niche providers targeting the same customer needs\n"
            "- New entrants leveraging technology or pricing to challenge incumbents"
        )
    if section == "financial_snapshot":
        return (
            f"{c} demonstrates a generally solid financial profile with diversified revenue streams, "
            f"ongoing investment in growth areas, and performance that is influenced by broader market conditions."
        )
    if section == "key_contacts":
        return (
            "Key contacts usually include executive leadership (CEO, CFO, CTO), line-of-business heads, "
            "and senior managers in HR, IT, and Procurement who influence or make purchasing decisions."
        )
    if section == "opportunities":
        return (
            "- Expand into new markets or customer segments\n"
            "- Launch adjacent products or services\n"
            "- Strengthen strategic partnerships and ecosystem relationships\n"
            "- Use data and analytics to improve customer experience and retention"
        )
    if section == "risks":
        return (
            "- Strong competition from existing and emerging players\n"
            "- Regulatory or compliance changes impacting operations\n"
            "- Macroeconomic factors affecting customer budgets\n"
            "- Technology shifts requiring continuous innovation and investment"
        )
    if section == "recommended_actions":
        return (
            f"- Engage {c} in strategic conversations around their current priorities and pain points\n"
            f"- Demonstrate clear business value and ROI when proposing solutions\n"
            f"- Build relationships with key stakeholders and decision-makers\n"
            f"- Share relevant case studies, references, and proof-of-value examples"
        )
    return ""


def ensure_all_sections_filled(sections: Dict[str, str], company_name: str) -> Dict[str, str]:
    required_keys = [
        "overview",
        "products_services",
        "market_position",
        "competitors",
        "financial_snapshot",
        "key_contacts",
        "opportunities",
        "risks",
        "recommended_actions",
    ]
    result: Dict[str, str] = {}

    for key in required_keys:
        value = sections.get(key, "")
        text = str(value).strip() if value is not None else ""
        lower = text.lower()

        if not text or lower in {"none", "null", "n/a", "undefined"}:
            text = _fallback_text(key, company_name)

        result[key] = text

    return result


def generate_agent_reply(
    user_message: str,
    company_name: str,
    current_plan: Optional[AccountPlan],
    chat_history: List[Dict[str, str]],
) -> Tuple[str, AccountPlan, List[Dict[str, str]]]:

    company_name = normalize_company_name(company_name)

    if current_plan is None:
        plan = AccountPlan.empty(company_name)
        research = research_company(company_name)
        raw_text = research.get("raw_answer", "")

        sections = split_into_sections(raw_text)
        sections = complete_missing_sections(sections)
        sections = ensure_all_sections_filled(sections, company_name)

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

    history_lines = []
    for msg in chat_history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_lines.append(f"{role.upper()}: {content}")
    history_text = "\n".join(history_lines) if history_lines else ""

    if target_section and wants_update:
        section_prompt = f"""
{SYSTEM_INSTRUCTIONS}

Company (use exactly this name in your answer): {company_name}

You are rewriting the '{target_section}' part.

Current text:
{plan_dict.get(target_section, "")}

User request:
{user_message}

Task:
- Rewrite only this section.
- Use a short 1–2 line intro, then markdown bullet points.
- Return ONLY the updated text for this section, nothing else.
"""
        new_text = call_gemini(section_prompt).strip()
        setattr(plan, target_section, new_text)

        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"
    else:
        prompt = f"""
{SYSTEM_INSTRUCTIONS}

Company (use exactly this name in your answer): {company_name}

Structured info:
{plan_dict}

Recent conversation:
{history_text}

User message:
{user_message}

Answer the user directly. Do not mention any 'account plan' or internal structures.
Use a short intro, then bullet points where useful.
Always refer to the company as: {company_name}.
"""
        reply = call_gemini(prompt)

    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return reply, plan, new_history
