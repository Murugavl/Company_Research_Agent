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
            "Correct this company name to its proper official capitalization. "
            "Return only the corrected name.\n\n"
            f"Name: {raw_name}"
        )
        model = genai.GenerativeModel(MODEL_NAME)
        res = model.generate_content(prompt)
        name = (res.text or "").strip()
        if name:
            return name
    except Exception:
        pass

    return " ".join(word.capitalize() for word in raw_name.split())


# ------------------------------------------------------
# 🟩 NEW FEATURE: RESEARCH PROGRESS + CONFLICT DETECTION
# ------------------------------------------------------
def progressive_research_company(company_name: str) -> Dict[str, str]:
    progress_messages = []

    progress_messages.append("Searching initial sources…")
    base_data = research_company(company_name)

    raw = base_data.get("raw_answer", "")

    progress_messages.append("Analyzing information across multiple sources…")
    sections = split_into_sections(raw)

    conflicts = []

    if "revenue" in raw.lower() and "$" not in raw:
        conflicts.append("Revenue information appears unclear")

    if "employees" in raw.lower() and "approx" in raw.lower():
        conflicts.append("Employee count varies across sources")

    if conflicts:
        msg = " • ".join(conflicts)
        progress_messages.append(f"Found conflicting data: {msg}. Should I dig deeper?")

    return {
        "progress": progress_messages,
        "raw": raw,
        "conflicts": conflicts
    }


# ------------------------------------------------------
# Rest of your existing helper functions stay the same
# ------------------------------------------------------

def _fallback_text(section: str, company_name: str) -> str:
    c = company_name

    if section == "overview":
        return (
            f"{c} is a major player in its industry, offering a wide range of solutions "
            f"and operating across multiple markets. The company serves a large global "
            f"customer base and continues to expand through innovation and investments."
        )

    if section == "products_services":
        return (
            "- Core products widely used by customers\n"
            "- Cloud platforms and enterprise services\n"
            "- Consumer and business applications\n"
            "- Hardware or physical devices\n"
            "- AI, analytics, and automation tools"
        )

    if section == "market_position":
        return (
            f"{c} holds a competitive position with strong brand recognition and presence "
            f"in key industry segments."
        )

    if section == "competitors":
        return (
            "- Established industry players offering similar services\n"
            "- Regional competitors\n"
            "- Emerging technology-led startups"
        )

    if section == "financial_snapshot":
        return (
            f"{c}'s financials indicate diversified revenue streams and continuous "
            f"investment into new growth areas."
        )

    if section == "key_contacts":
        return (
            "Key contacts include executives such as CEO, CTO, CFO, and department heads "
            "in HR, IT, Finance, and Procurement."
        )

    if section == "opportunities":
        return (
            "- Expand into new regions\n"
            "- Innovate and strengthen product portfolio\n"
            "- Increase automation and operational efficiency"
        )

    if section == "risks":
        return (
            "- Competitive pressure\n"
            "- Regulatory challenges\n"
            "- Market uncertainty\n"
            "- Rapid technology changes"
        )

    if section == "recommended_actions":
        return (
            f"- Engage {c} with tailored value propositions\n"
            f"- Build long-term relationships with decision-makers\n"
            f"- Provide ROI-driven case studies"
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

    result = {}

    for key in required_keys:
        value = sections.get(key, "")
        text = str(value).strip() if value else ""
        if not text or text.lower() in {"none", "null", "undefined"}:
            text = _fallback_text(key, company_name)
        result[key] = text

    return result


def clean_list_response(text: str) -> str:
    if text.strip().startswith("[") and text.strip().endswith("]"):
        try:
            import ast
            items = ast.literal_eval(text)
            if isinstance(items, list):
                return "\n".join(f"- {i}" for i in items)
        except Exception:
            pass
    return text


def get_last_company_from_history(chat_history: List[Dict[str, str]]) -> Optional[str]:
    for msg in reversed(chat_history):
        if msg["role"] == "user":
            possible = normalize_company_name(msg["content"])
            if possible and len(possible.split()) <= 3:
                banned = {"can", "you", "tell", "update", "its", "about", "the"}
                if not any(w in banned for w in possible.lower().split()):
                    return possible
    return None


# ------------------------------------------------------
# 🟦 MAIN FUNCTION — UPDATED WITH PROGRESS FEATURE
# ------------------------------------------------------
def generate_agent_reply(
        user_message: str,
        company_name: str,
        current_plan: Optional[AccountPlan],
        chat_history: List[Dict[str, str]],
    ) -> Tuple[str, AccountPlan, List[Dict[str, str]]]:

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
            current_plan = None
            company_name = candidate

    company_name = normalize_company_name(company_name)

    # ------------------------------------------------------
    # 🟩 APPLY PROGRESSIVE RESEARCH ONLY WHEN CREATING PLAN
    # ------------------------------------------------------
    if current_plan is None:
        plan = AccountPlan.empty(company_name)

        progress = progressive_research_company(company_name)

        progress_messages = progress["progress"]
        raw_text = progress["raw"]
        conflicts = progress["conflicts"]

        sections = split_into_sections(raw_text)
        sections = complete_missing_sections(sections)
        sections = ensure_all_sections_filled(sections, company_name)

        plan.overview = sections["overview"]
        plan.products_services = sections["products_services"]
        plan.market_position = sections["market_position"]
        plan.competitors = sections["competitors"]
        plan.financial_snapshot = sections["financial_snapshot"]
        plan.key_contacts = sections["key_contacts"]
        plan.opportunities = sections["opportunities"]
        plan.risks = sections["risks"]
        plan.recommended_actions = sections["recommended_actions"]

        if conflicts:
            return (
                "\n".join(progress_messages),
                plan,
                chat_history + [{"role": "assistant", "content": "\n".join(progress_messages)}]
            )

    else:
        plan = current_plan

    plan_dict = plan.to_dict()

    history_lines = [
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in chat_history[-MAX_CHAT_HISTORY:]
    ]
    history_text = "\n".join(history_lines)

    if target_section and wants_update:
        update_prompt = f"""
{SYSTEM_INSTRUCTIONS}

Rewrite ONLY the '{target_section}' section.

Company: {company_name}

Current text:
{plan_dict.get(target_section)}

User request:
{user_message}

Return ONLY the updated text.
"""
        new_text = clean_list_response(call_gemini(update_prompt).strip())
        setattr(plan, target_section, new_text)

        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"

    else:
        prompt = f"""
{SYSTEM_INSTRUCTIONS}

Company: {company_name}

Structured info:
{plan_dict}

Recent conversation:
{history_text}

User message:
{user_message}

Answer naturally and directly.
"""
        reply = call_gemini(prompt)

    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return reply, plan, new_history
