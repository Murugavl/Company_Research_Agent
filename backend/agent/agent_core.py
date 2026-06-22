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
- Answer naturally and professionally.
- On a new company research request, the chat reply (on the left side) should ONLY contain the executive overview/summary of the company in a brief, premium summary or short description. Do not list out all other sections (like products/services, market position, opportunities, etc.) in the chat reply.
- When the user asks to update, modify, or get more details on a specific section, rewrite ONLY that section based on the request and return the updated text.
- Never use '#' or markdown headers (like #, ##, ###) for any headings. Instead, use bold text (like **Heading Name**) for all headings.
- Keep the tone concise, clear, and business-focused.
- Never reuse any text from earlier answers.
- Only talk about the company currently mentioned by the user.
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
    "locations": ["location", "branch", "office", "headquarter", "presence"],
}

UPDATE_KEYWORDS = [
    "update", "change", "edit", "modify", "rewrite", "revise", 
    "detail", "details", "elaborate", "expand", "add", "more about", 
    "tell me more", "more info", "more information", "give info", 
    "provide info", "remove", "delete", "clear", "wipe", "exclude", 
    "omit"
]

COMMON_CUSTOM_SECTIONS = {
    'history', 'founding', 'founding story', 'background', 'origin', 'origins',
    'culture', 'work environment', 'values', 'workplace',
    'technology', 'tech stack', 'technology stack', 'infrastructure', 'architecture',
    'sustainability', 'esg', 'environment', 'environmental',
    'customers', 'clients', 'partnerships', 'partners',
    'funding', 'investment', 'investors', 'ipo',
    'supply chain', 'manufacturing', 'logistics',
    'legal', 'legal issues', 'controversies', 'lawsuits',
    'future plans', 'roadmap', 'vision', 'strategy'
}

def detect_target_section(user_message: str) -> Optional[str]:
    import re
    msg = user_message.lower()
    order = [
        "products_services", "market_position", "competitors", "financial_snapshot",
        "key_contacts", "opportunities", "risks", "recommended_actions", "locations", "overview"
    ]
    for section in order:
        words = SECTION_KEYWORDS[section]
        for w in words:
            if w == "about the company":
                # Only match "about the company" if it's the end of the query or followed by overview/summary/itself
                pattern = r"\babout the company\b(?:\s+(?:itself|overview|summary|details))?\s*\??$"
                if re.search(pattern, msg):
                    return section
            else:
                # Use starting word boundary to avoid substring match (e.g. "frisk" -> "risk")
                if re.search(r"\b" + re.escape(w), msg):
                    return section
    return None

def is_update_intent(user_message: str) -> bool:
    msg = user_message.lower()
    return any(w in msg for w in UPDATE_KEYWORDS)

TELL_ME_ABOUT_PATTERN = [
    r'tell me (?:more )?about (?:the )?(?:company(?:\'s)? )?(.+?)(?:\s+(?:of|for|in|at|by|from|with)\b.+)?$',
    r'(?:give|provide|show) me (?:the )?(?:company(?:\'s)? )?(.+?) (?:info(?:rmation)?|data|details?|section)',
    r'(?:what(?:\'s| is) the )?company(?:\'s)? (.+?)(?:\?|$)',
    r'add (?:a |the )?(.+?) section',
    r'include (?:the )?(.+?) (?:section|info)',
]

STANDARD_SECTION_NAMES = {
    'overview', 'summary', 'about', 'products', 'services', 'products and services',
    'market', 'position', 'market position', 'competitors', 'competition',
    'financial', 'financials', 'finance', 'financial snapshot', 'revenue', 'profit',
    'contacts', 'key contacts', 'stakeholders', 'opportunities', 'growth',
    'risks', 'challenges', 'recommended actions', 'recommendations',
    'locations', 'offices', 'headquarters', 'branches'
}

def _extract_section_from_pattern(user_message: str) -> Optional[str]:
    """Fast regex-based extraction of section name from 'tell me about X' patterns."""
    import re
    msg = user_message.lower().strip().rstrip('?.')
    for pattern in TELL_ME_ABOUT_PATTERN:
        m = re.search(pattern, msg, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Remove leading possessive/determiner words
            candidate = re.sub(r'^(?:their|its|this|the|a|an)\s+', '', candidate)
            # Skip if it matches a standard section name
            if candidate.lower() in STANDARD_SECTION_NAMES:
                return None
            # Skip common stop-word-only results
            if candidate.lower() in {'it', 'them', 'this', 'that', 'they', 'company', 'business', 'firm'}:
                return None
            # Skip if too long or too short
            if 3 <= len(candidate) <= 40:
                # Capitalize properly
                return ' '.join(w.capitalize() for w in candidate.split())
    return None

def extract_custom_section_name(user_message: str) -> Optional[str]:
    # First try fast regex extraction
    fast_result = _extract_section_from_pattern(user_message)
    if fast_result:
        # Check if it contains any common custom section keywords
        words = set(fast_result.lower().split())
        if any(w in COMMON_CUSTOM_SECTIONS for w in words) or fast_result.lower() in COMMON_CUSTOM_SECTIONS:
            return fast_result
    
    # Analyze user message to extract clean custom section name.
    prompt = f"""
    Analyze the user message to see if they are asking to add, update, retrieve, or learn about a new specific topic or section for a company profile that is NOT one of these standard sections:
    - Overview, Products & Services, Market Position, Competitors, Financial Snapshot, Key Contacts, Opportunities, Risks, Recommended Actions, Locations

    Examples of NEW topics/sections to detect (not in the standard list above):
    - history, founding story, background, origin
    - culture, work environment, values
    - technology stack, tech stack, infrastructure
    - sustainability, ESG, environment
    - customers, clients, partnerships
    - funding, investment, investors
    - supply chain, manufacturing
    - legal issues, controversies
    - future plans, roadmap

    If the user is asking about a new topic or section like those above, return ONLY the clean capitalized name (e.g., "History", "Company Culture", "Technology Stack").
    If the message matches a standard section, is general chat, or is unclear, return "NONE".

    User message: "{user_message}"
    
    Clean topic name or "NONE":
    """
    try:
        response = groq_client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        ans = response.choices[0].message.content.strip() if response.choices else "NONE"
        if ans.upper() == "NONE" or not ans:
            return None
        # Clean it up: remove quotes, periods, and ensure it's not too long
        ans = ans.replace('"', '').replace("'", "").replace(".", "").replace("**", "").replace("*", "").strip()
        if len(ans) > 40:
            return None
        return ans
    except Exception as e:
        logger.error(f"Error extracting custom section name: {e}")
        return None

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

def preprocess_agent_request(
    user_message: str,
    company_name: str,
    current_plan: Optional[AccountPlan],
    chat_history: List[Dict[str, str]]
) -> Tuple[str, Optional[str], bool, bool]:
    target_section = detect_target_section(user_message)
    is_custom_section = False
    wants_update = is_update_intent(user_message)
    
    if current_plan:
        if current_plan.extra_sections:
            msg_lower = user_message.lower()
            for custom_name in current_plan.extra_sections.keys():
                if custom_name.lower() in msg_lower:
                    target_section = custom_name
                    is_custom_section = True
                    break
        
        if not target_section:
            extracted = extract_custom_section_name(user_message)
            if extracted:
                target_section = extracted
                is_custom_section = True

    is_section_request = (target_section is not None)
    
    if is_section_request and current_plan:
        wants_update = True
        last_company = get_last_company_from_history(chat_history)
        if last_company:
            company_name = last_company
    else:
        candidate = normalize_company_name(user_message)
        banned = {
            "can", "you", "tell", "about", "update", "its", "the", "edit", "hello", "hi", "hey",
            "founding", "history", "culture", "funding", "technology", "sustainability", 
            "competitor", "competitors", "competition", "product", "products", "service", "services", 
            "market", "position", "financial", "financials", "finance", "revenue", "profit", 
            "contact", "contacts", "opportunity", "opportunities", "risk", "risks", 
            "recommendation", "recommendations", "location", "locations", "overview", "summary"
        }
        if candidate and not any(w in banned for w in candidate.lower().split()):
            if candidate.lower() != company_name.lower():
                current_plan = None
            company_name = candidate

    company_name = normalize_company_name(company_name)
    return company_name, target_section, wants_update, is_custom_section

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
    
    company_name, target_section, wants_update, is_custom_section = preprocess_agent_request(
        user_message, company_name, current_plan, chat_history
    )

    # Specific section update request on an existing plan
    if current_plan and target_section and wants_update:
        logger.info(f"Rapid update for section: {target_section} - {company_name} (custom: {is_custom_section})")
        
        # Check if it's a request to delete/remove the entire section
        is_entire_deletion = False
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ["remove", "delete", "clear", "wipe", "exclude", "omit"]):
            if len(msg_lower) < 65 and not any(w in msg_lower for w in ["point", "bullet", "paragraph", "line", "sentence", "specific"]):
                is_entire_deletion = True
                
        current_text = current_plan.extra_sections.get(target_section, "") if is_custom_section else getattr(current_plan, target_section, "")
        
        if is_entire_deletion:
            new_text = ""
        else:
            needs_research = any(w in user_message.lower() for w in ["detail", "more", "expand", "update", "add", "elaborate", "fetch", "get", "tell me", "what is"])
            if is_custom_section:
                needs_research = True
                
            research_context = ""
            if needs_research:
                try:
                    from .tools import tavily_search
                    search_query = f"{company_name} {target_section} {user_message}"
                    res = await tavily_search(search_query)
                    answer = res.get("answer", "")
                    snippets = "\n".join([f"- {r.get('content', '')}" for r in res.get("results", [])])
                    research_context = f"{answer}\n\nRELEVANT SNIPPETS:\n{snippets}"
                except Exception as e:
                    logger.error(f"Tavily search during update failed: {e}")
                    
            update_prompt = f"""
{SYSTEM_INSTRUCTIONS}
Rewrite ONLY the '{target_section}' section.
Company: {company_name}
Current text of this section: {current_text}
New research info: {research_context}
User request: {user_message}

Rules for update:
- Expand, correct, update, or remove content in the current text as specified by the user request.
- If the user request asks to remove this section entirely, return an empty string.
- If the user request asks to remove specific points, return the text with those points removed.
- Use the new research info if provided to enrich the text with fresh, specific facts, names, and details.
- Never use '#' or markdown headers (like #, ##, ###) for headings. Instead, use bold text (like **Heading Name**) for all headings.
- Return ONLY the updated section text (or an empty string if the section is deleted). Do not include any introductory or explanatory text.
"""
            new_text = call_groq(update_prompt).strip()
            
        # Update the plan object
        if is_custom_section:
            if not current_plan.extra_sections:
                current_plan.extra_sections = {}
            if is_entire_deletion:
                if target_section in current_plan.extra_sections:
                    del current_plan.extra_sections[target_section]
            else:
                current_plan.extra_sections[target_section] = new_text
        else:
            setattr(current_plan, target_section, new_text)
            
        # Compute dynamic diff
        diff_result = {}
        old_val_str = str(current_text).strip()
        new_val_str = str(new_text).strip()
        if old_val_str != new_val_str:
            diff_result[target_section] = {"old": old_val_str, "new": new_val_str}
            
        reply = f"The {target_section.replace('_', ' ').title()} section has been removed." if is_entire_deletion else f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{new_text}"
        new_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": reply},
        ]
        return reply, current_plan, new_history, diff_result

    # Otherwise, perform research using LangGraph
    logger.info(f"Invoking research graph for {company_name}")
    
    initial_state = {
        "user_message": user_message,
        "company_name": company_name,
        "session_id": session_id,
        "chat_history": chat_history,
        "current_plan": current_plan.model_dump() if current_plan else None,
        "raw_research": "",
        "images": [],
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
            company_name=str(result.get("company_name", company_name)),
            overview=str(final_sections.get("overview", "")),
            products_services=str(final_sections.get("products_services", "")),
            market_position=str(final_sections.get("market_position", "")),
            competitors=str(final_sections.get("competitors", "")),
            financial_snapshot=str(final_sections.get("financial_snapshot", "")),
            key_contacts=str(final_sections.get("key_contacts", "")),
            opportunities=str(final_sections.get("opportunities", "")),
            risks=str(final_sections.get("risks", "")),
            recommended_actions=str(final_sections.get("recommended_actions", "")),
            locations=str(final_sections.get("locations", "")),
            company_images=final_sections.get("company_images", []),
            sources=final_sections.get("sources", []),
            extra_sections=final_sections.get("extra_sections", {})
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

async def call_groq_stream(prompt: str):
    """Async generator to stream tokens from Groq."""
    response = groq_client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=2000,
        stream=True
    )
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

async def generate_agent_reply_stream(
        user_message: str,
        company_name: str,
        current_plan: Optional[AccountPlan],
        chat_history: List[Dict[str, str]],
        session_id: str
    ):
    """
    Async generator that performs research and then streams the reply tokens.
    Final yield is the plan and diff metadata.
    """
    # 1. Preprocessing
    company_name, target_section, wants_update, is_custom_section = preprocess_agent_request(
        user_message, company_name, current_plan, chat_history
    )

    # Handle Rapid Update
    if current_plan and target_section and wants_update:
        # Check if it's a request to delete/remove the entire section
        is_entire_deletion = False
        msg_lower = user_message.lower()
        if any(w in msg_lower for w in ["remove", "delete", "clear", "wipe", "exclude", "omit"]):
            if len(msg_lower) < 65 and not any(w in msg_lower for w in ["point", "bullet", "paragraph", "line", "sentence", "specific"]):
                is_entire_deletion = True
                
        current_text = current_plan.extra_sections.get(target_section, "") if is_custom_section else getattr(current_plan, target_section, "")
        
        if is_entire_deletion:
            full_reply = f"The {target_section.replace('_', ' ').title()} section has been removed."
            yield {"type": "token", "content": full_reply}
        else:
            needs_research = any(w in user_message.lower() for w in ["detail", "more", "expand", "update", "add", "elaborate", "fetch", "get", "tell me", "what is"])
            if is_custom_section:
                needs_research = True
                
            research_context = ""
            if needs_research:
                try:
                    from .tools import tavily_search
                    search_query = f"{company_name} {target_section} {user_message}"
                    res = await tavily_search(search_query)
                    answer = res.get("answer", "")
                    snippets = "\n".join([f"- {r.get('content', '')}" for r in res.get("results", [])])
                    research_context = f"{answer}\n\nRELEVANT SNIPPETS:\n{snippets}"
                except Exception as e:
                    logger.error(f"Tavily search during update failed: {e}")
                    
            prompt = f"""
{SYSTEM_INSTRUCTIONS}
Rewrite ONLY the '{target_section}' section.
Company: {company_name}
Current text of this section: {current_text}
New research info: {research_context}
User request: {user_message}

Rules for update:
- Expand, correct, update, or remove content in the current text as specified by the user request.
- If the user request asks to remove this section entirely, return an empty string.
- If the user request asks to remove specific points, return the text with those points removed.
- Use the new research info if provided to enrich the text with fresh, specific facts, names, and details.
- Never use '#' or markdown headers (like #, ##, ###) for headings. Instead, use bold text (like **Heading Name**) for all headings.
- Return ONLY the updated section text (or an empty string if the section is deleted). Do not include any introductory or explanatory text.
"""
            full_reply = ""
            try:
                async for token in call_groq_stream(prompt):
                    full_reply += token
                    yield {"type": "token", "content": token}
            except Exception as e:
                logger.error(f"Rapid update streaming failed: {e}")
                error_msg = str(e)
                friendly_error = "I encountered a temporary service interruption while updating the section. Please try again."
                if "429" in error_msg:
                    friendly_error = "Rate limit reached. Please wait a moment before trying again."
                yield {"type": "token", "content": friendly_error}
                return
        
        # Update the plan object
        new_text = "" if is_entire_deletion else full_reply.strip()
        if is_custom_section:
            if not current_plan.extra_sections:
                current_plan.extra_sections = {}
            if is_entire_deletion:
                if target_section in current_plan.extra_sections:
                    del current_plan.extra_sections[target_section]
            else:
                current_plan.extra_sections[target_section] = new_text
        else:
            setattr(current_plan, target_section, new_text)
            
        # Compute dynamic diff
        diff_result = {}
        old_val_str = str(current_text).strip()
        new_val_str = str(new_text).strip()
        if old_val_str != new_val_str:
            diff_result[target_section] = {"old": old_val_str, "new": new_val_str}
        
        # Prepare final output
        final_reply = full_reply if is_entire_deletion else f"Here is the updated {target_section.replace('_', ' ').title()} section:\n\n{full_reply.strip()}"
        new_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": final_reply},
        ]
        
        yield {
            "type": "plan",
            "plan": current_plan.model_dump(),
            "diff_result": diff_result,
            "chat_history": new_history,
            "company_name": company_name
        }
        return

    # Handle Full Research using Graph logic
    initial_state = {
        "user_message": user_message,
        "company_name": company_name,
        "session_id": session_id,
        "chat_history": chat_history,
        "current_plan": current_plan.model_dump() if current_plan else None,
        "raw_research": "",
        "images": [],
        "sections_base": {},
        "sections_enriched": {},
        "final_sections": {},
        "reply": "",
        "diff_result": {},
        "conflicts": [],
        "error": None,
        "sources": []
    }

    try:
        # We run the graph up to the merge node to get the plan
        # Then we stream the reply manually for better control
        from .nodes import node_normalize, node_research, node_split, node_complete, node_merge, node_save, node_reply
        
        # Sequential execution for streaming context
        s1 = await node_normalize(initial_state)
        initial_state.update(s1)
        
        s2 = await node_research(initial_state)
        initial_state.update(s2)
        
        # Run split and complete in parallel
        sb_task = asyncio.create_task(node_split(initial_state))
        se_task = asyncio.create_task(node_complete(initial_state))
        sb, se = await asyncio.gather(sb_task, se_task)
        initial_state.update(sb)
        initial_state.update(se)
        
        s_merge = await node_merge(initial_state)
        initial_state.update(s_merge)
        
        # Now stream the reply using only the Executive Overview section to prevent 413 TPM overflow
        overview_text = initial_state["final_sections"].get("overview", "")
        prompt = f"""
{SYSTEM_INSTRUCTIONS}
Company: {initial_state['company_name']}
Executive Overview: {overview_text}
Chat History: {initial_state['chat_history']}
User message: {initial_state['user_message']}

Answer naturally and professionally based on the research.
"""
        full_reply = ""
        try:
            async for token in call_groq_stream(prompt):
                full_reply += token
                yield {"type": "token", "content": token}
        except Exception as e:
            logger.error(f"Reply streaming failed: {e}")
            error_msg = str(e)
            friendly_error = "Intelligence gathered successfully. The canvas on the right has been updated. (Note: The text summary hit a temporary rate limit.)"
            if "429" in error_msg:
                friendly_error = f"Intelligence gathered successfully on {initial_state['company_name']}! The canvas on the right has been updated with the latest research. (Note: The natural language summary hit a temporary Groq rate limit, but your core plan data is ready.)"
            yield {"type": "token", "content": friendly_error}
            full_reply = friendly_error
            
        initial_state["reply"] = full_reply.strip()
        
        # Run save and diff
        s_save = await node_save(initial_state)
        initial_state.update(s_save)
        
        # Final plan yield
        final_sections = initial_state["final_sections"]
        plan_out = AccountPlan(
            company_name=str(initial_state.get("company_name", company_name)),
            overview=str(final_sections.get("overview", "")),
            products_services=str(final_sections.get("products_services", "")),
            market_position=str(final_sections.get("market_position", "")),
            competitors=str(final_sections.get("competitors", "")),
            financial_snapshot=str(final_sections.get("financial_snapshot", "")),
            key_contacts=str(final_sections.get("key_contacts", "")),
            opportunities=str(final_sections.get("opportunities", "")),
            risks=str(final_sections.get("risks", "")),
            recommended_actions=str(final_sections.get("recommended_actions", "")),
            locations=str(final_sections.get("locations", "")),
            company_images=final_sections.get("company_images", []),
            sources=final_sections.get("sources", []),
            extra_sections=final_sections.get("extra_sections", {})
        )
        
        new_history = chat_history + [
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": initial_state["reply"]},
        ]
        
        yield {
            "type": "plan",
            "plan": plan_out.model_dump(),
            "diff_result": initial_state.get("diff_result", {}),
            "chat_history": new_history,
            "company_name": initial_state["company_name"]
        }

    except Exception as e:
        logger.error(f"Streaming research failed: {e}", exc_info=True)
        error_msg = str(e)
        friendly_error = "The strategic engine is currently experiencing high volume. Please wait a moment and try again."
        if "429" in error_msg:
            friendly_error = "Intelligence rate limit reached. Please pause for 60 seconds before initiating a new scan."
        yield {"type": "token", "content": friendly_error}

