import os
from typing import List, Dict, Any, Tuple, Optional

import google.generativeai as genai
from dotenv import load_dotenv

from .account_plan import AccountPlan
from .tools import research_company

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"

# basic behavior instructions for the model
SYSTEM_INSTRUCTIONS = """
You are a helpful Company Research Assistant and Account Plan Generator.

Your goals:
1. Help the user research a specific company through natural, friendly conversation.
2. Use the available account plan data to give structured, business-relevant answers.
3. When the plan is empty or incomplete, assume that a separate research tool has already
   collected basic information and populated the plan.
4. If information might be uncertain, outdated, or conflicting, explicitly say that and
   ask the user if you should dig deeper or focus on a specific area.
5. Allow the user to update specific sections of the account plan through natural language.
   For example: "update the risks section" or "rewrite the opportunities focusing on AI".
6. Keep your tone professional but conversational, like a smart business analyst.
7. If the user goes off-topic or asks for something beyond your capabilities, gently
   explain the limitation and steer the conversation back to company research.

Always:
- Refer to the current account plan when answering.
- Be transparent when you are making reasonable assumptions.
- Encourage the user to refine or correct sections of the plan.
"""

# keyword map for updating sections
SECTION_KEYWORDS = {
    "overview": ["overview", "summary", "about the company", "intro"],
    "products_services": ["product", "service", "offerings", "solutions"],
    "market_position": ["market", "position", "branding", "segment"],
    "competitors": ["competitor", "competition", "rival"],
    "financial_snapshot": ["financial", "revenue", "profit", "loss", "funding"],
    "key_contacts": ["contact", "person", "stakeholder", "decision maker"],
    "opportunities": ["opportunity", "growth", "expansion", "upside"],
    "risks": ["risk", "challenge", "threat", "downside"],
    "recommended_actions": ["recommendation", "action", "next step", "plan"]
}

# detect the section that user wants to change
def detect_target_section(user_message: str) -> Optional[str]:
    lower_msg = user_message.lower()
    for section, keywords in SECTION_KEYWORDS.items():
        for kw in keywords:
            if kw in lower_msg:
                return section
    return None

# gemini model calling
def call_gemini(prompt: str) -> str:
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text.strip() if response.text else ""

# agent function
def generate_agent_reply(
    user_message: str,
    company_name: str,
    current_plan: Optional[AccountPlan],
    chat_history: List[Dict[str, str]]) -> Tuple[str, AccountPlan, List[Dict[str, str]]]:
    
    # creation of  initial plan if it is missing
    if current_plan is None:
        plan = AccountPlan.empty(company_name)
        research = research_company(company_name)
        raw_text = research.get("raw_answer", "")

        plan.overview = raw_text
        plan.products_services = raw_text
        plan.market_position = raw_text
        plan.competitors = raw_text
        plan.financial_snapshot = raw_text
        plan.key_contacts = raw_text
        plan.opportunities = raw_text
        plan.risks = raw_text
        plan.recommended_actions = raw_text

        system_note = (
            "Note: I have just generated an initial account plan for this company "
            "based on mock research data. Explain the key insights and tell the "
            "user they can ask to refine or update any specific section."
        )
    else:
        plan = current_plan
        system_note = (
            "Note: An account plan already exists. Use it to answer the user and, "
            "if they ask to change a specific section, propose a refined version "
            "of that section and explain what changed."
        )

    # see if user wants to edit a specific section
    target_section = detect_target_section(user_message)

    # prepare short chat history
    history_text_parts = []
    for msg in chat_history[-6:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        history_text_parts.append(f"{role.upper()}: {content}")

    history_text = "\n".join(history_text_parts) if history_text_parts else "No previous conversation."

    plan_dict = plan.to_dict()

    prompt = f"""
                SYSTEM INSTRUCTIONS:
                {SYSTEM_INSTRUCTIONS}

                ADDITIONAL SYSTEM NOTE:
                {system_note}

                COMPANY NAME:
                {company_name}

                CURRENT ACCOUNT PLAN (JSON-like):
                {plan_dict}

                CONVERSATION HISTORY (most recent messages):
                {history_text}

                USER MESSAGE:
                {user_message}

                If the user seems to be asking to update or rewrite a specific section, focus on that section.
                Always answer in a clear, structured way. If you are updating a section, clearly state which
                section you are updating and provide the new suggested text for that section.
                """

    reply = call_gemini(prompt)

    # updation of section if needed
    if target_section is not None:
        try:
            updated_prompt = f"""
                                You are updating the '{target_section}' section of this account plan.

                                CURRENT SECTION TEXT:
                                {plan_dict.get(target_section, "")}

                                USER REQUEST:
                                {user_message}

                                TASK:
                                Rewrite ONLY the '{target_section}' section in a clear, business-friendly way that
                                respects the user's request. Return ONLY the new text for that section, nothing else.
                                """
            new_section_text = call_gemini(updated_prompt)

            setattr(plan, target_section, new_section_text.strip())

            reply = (
                reply
                + "\n\n"
                + f"(I have updated the **{target_section.replace('_', ' ').title()}** section of the account plan.)"
            )
        except Exception:
            reply = (
                reply
                + "\n\n"
                + "(I tried to update a section of the plan, but something went wrong. "
                  "You can ask again more specifically if needed.)"
            )

    # chat memory updation
    new_history = chat_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": reply},
    ]

    return reply, plan, new_history
