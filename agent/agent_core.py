import os
from typing import List, Dict, Tuple, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .account_plan import AccountPlan
from .tools import *
from .logger import logger


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
    logger.info(f"[detect_target_section] user_message={user_message}")
    msg = user_message.lower()
    for section, words in SECTION_KEYWORDS.items():
        for w in words:
            if w in msg:
                logger.info(f"[detect_target_section] Detected section={section}")
                return section
    logger.info("[detect_target_section] No section detected")
    return None


def is_update_intent(user_message: str) -> bool:
    logger.info(f"[is_update_intent] user_message={user_message}")
    msg = user_message.lower()
    result = any(w in msg for w in UPDATE_KEYWORDS)
    logger.info(f"[is_update_intent] intent={result}")
    return result


def call_gemini(prompt: str) -> str:
    logger.info("[call_gemini] Sending prompt to Gemini")
    model = genai.GenerativeModel(MODEL_NAME)
    res = model.generate_content(prompt)
    reply = res.text.strip() if res.text else ""
    logger.info(f"[call_gemini] Received response_length={len(reply)}")
    return reply


def normalize_company_name(raw_name: str) -> str:
    logger.info(f"[normalize_company_name] raw_name={raw_name}")
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
            logger.info(f"[normalize_company_name] normalized={name}")
            return name
    except Exception as e:
        logger.error(f"[normalize_company_name] Error={e}")

    fallback = " ".join(word.capitalize() for word in raw_name.split())
    logger.info(f"[normalize_company_name] fallback={fallback}")
    return fallback


def _fallback_text(section: str, company_name: str) -> str:
    logger.warning(f"[fallback] Missing content for section={section}")
    c = company_name

    if section == "overview":
        return (
            f"{c} is a major player in its industry, offering a wide range of solutions and operating "
            f"across multiple markets. The company serves a large global customer base and has a workforce "
            f"that typically falls within broad reported ranges (employee counts often vary by source). "
            f"It continues to expand its capabilities through new technology, strategic investments, and "
            f"improvements in operational efficiency. {c} maintains a strong presence in its sector by "
            f"focusing on innovation, customer reach, and long-term growth opportunities."
        )

    if section == "products_services":
        return (
            "- Core Products & Platforms: Primary offerings used by the majority of customers.\n"
            "- Cloud & Enterprise Services: Hosted platforms, tools, and business solutions.\n"
            "- Software & Applications: Consumer and enterprise apps that support daily operations.\n"
            "- Hardware & Devices: Physical products that extend the software ecosystem.\n"
            "- AI & Analytics: Data-driven tools, automation systems, and machine-learning capabilities."
        )

    if section == "market_position":
        return (
            f"{c} holds a competitive position in its market, with established brand recognition, "
            f"presence across key industry segments, and differentiation through technology, quality, "
            f"or customer reach."
        )

    if section == "competitors":
        return (
            "- Established companies offering similar products and services\n"
            "- Regional or niche providers addressing specific market needs\n"
            "- Emerging players leveraging technology or pricing to compete"
        )

    if section == "financial_snapshot":
        return (
            f"{c} demonstrates a generally strong financial profile, with diversified revenue sources, "
            f"investment in strategic growth areas, and financial results influenced by broader "
            f"market and economic conditions."
        )

    if section == "key_contacts":
        return (
            "Key contacts typically include executive leadership (CEO, CFO, CTO), business unit heads, "
            "and decision-makers in HR, IT, Finance, and Procurement."
        )

    if section == "opportunities":
        return (
            "- Enter new geographical or industry markets\n"
            "- Expand product or service portfolio\n"
            "- Strengthen ecosystem partnerships\n"
            "- Increase automation and data-driven decision-making"
        )

    if section == "risks":
        return (
            "- Competition from established and emerging players\n"
            "- Regulatory or compliance challenges\n"
            "- Market uncertainty impacting customer budgets\n"
            "- Rapid technology changes requiring ongoing innovation"
        )

    if section == "recommended_actions":
        return (
            f"- Engage {c} in strategic discussions about key priorities\n"
            f"- Demonstrate ROI and clear business value\n"
            f"- Build and maintain relationships with decision-makers\n"
            f"- Provide case studies and success examples"
        )

    return ""


def ensure_all_sections_filled(sections: Dict[str, str], company_name: str) -> Dict[str, str]:
    logger.info("[ensure_all_sections_filled] Checking sections")
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
        if not value or str(value).strip() == "":
            logger.warning(f"[ensure_all_sections_filled] Auto-filling missing section={key}")
        result[key] = value or _fallback_text(key, company_name)

    return result

def detect_high_conflict(raw_text: str) -> Optional[str]:
    text = raw_text.lower()

    # Only trigger for true contradictions (NOT uncertainty)
    contradiction_pairs = [
        ("increase", "decrease"),
        ("grew", "declined"),
        ("profit", "loss"),
        ("expansion", "cutback"),
    ]

    for a, b in contradiction_pairs:
        if a in text and b in text:
            return "I'm finding conflicting information across sources. Should I dig deeper?"

    # Trigger only for BIG numerical mismatches (>=50%)
    import re
    nums = re.findall(r"\d[\d,\.]*", raw_text)
    cleaned = []
    for n in nums:
        try:
            cleaned.append(float(n.replace(",", "")))
        except:
            pass

    if len(cleaned) >= 2:
        lo, hi = min(cleaned), max(cleaned)
        if hi > 0 and (hi - lo) >= hi * 0.50:  # 50% gap = real conflict
            return "Some reported numbers differ significantly across sources. Should I dig deeper?"

    return None



def generate_agent_reply(
    user_message: str,
    company_name: str,
    current_plan: Optional[AccountPlan],
    chat_history: List[Dict[str, str]],
) -> Tuple[str, AccountPlan, List[Dict[str, str]]]:

    logger.info(f"[generate_agent_reply] user_message={user_message}, company_name={company_name}")

    normalized_from_msg = normalize_company_name(user_message)

    # Only switch if user is clearly asking about a new company
    if any(keyword in user_message.lower() for keyword in ["tell me about", "about ", "company"]):
        if normalized_from_msg.lower() != company_name.lower():
            current_plan = None
            company_name = normalized_from_msg


    company_name = normalize_company_name(company_name)

    if current_plan is None:
        logger.info("[generate_agent_reply] Creating new plan")
        plan = AccountPlan.empty(company_name)

        research = research_company(company_name)
        logger.info("[generate_agent_reply] Research completed")

        raw_text = research.get("raw_answer", "")

        conflict_msg = detect_high_conflict(raw_text)
        if conflict_msg:
            logger.info("[generate_agent_reply] Conflict detected")
            reply = conflict_msg
            new_history = chat_history + [{"role": "assistant", "content": reply}]
            return reply, None, new_history

        sections = split_into_sections(raw_text)
        sections = complete_missing_sections(sections)
        sections = ensure_all_sections_filled(sections, company_name)

        # assign
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
        logger.info("[generate_agent_reply] Using existing plan")
        plan = current_plan

    plan_dict = plan.to_dict()

    target_section = detect_target_section(user_message)
    wants_update = is_update_intent(user_message)

    logger.info(f"[generate_agent_reply] target_section={target_section}, wants_update={wants_update}")

    history_lines = [
        f"{m.get('role','').upper()}: {m.get('content','')}"
        for m in chat_history[-6:]
    ]
    history_text = "\n".join(history_lines)

    if target_section and wants_update:
        logger.info(f"[generate_agent_reply] Updating section={target_section}")
        section_prompt = f"""
{SYSTEM_INSTRUCTIONS}

Rewrite ONLY the '{target_section}' section.

Company: {company_name}

Current text:
{plan_dict.get(target_section)}

User request:
{user_message}

Return ONLY the updated text.
"""
        new_text = call_gemini(section_prompt).strip()
        setattr(plan, target_section, new_text)

        reply = f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"

    else:
        logger.info("[generate_agent_reply] Generating natural answer")
        prompt = f"""
{SYSTEM_INSTRUCTIONS}

Company: {company_name}

Structured info:
{plan_dict}

Recent conversation:
{history_text}

User message:
{user_message}

Answer naturally and directly. Do not mention internal structures.
"""
        reply = call_gemini(prompt)

    logger.info("[generate_agent_reply] Reply generated")

    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    logger.info("[generate_agent_reply] History updated")

    return reply, plan, new_history
