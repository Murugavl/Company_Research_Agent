import os
import json
import requests
from dotenv import load_dotenv
from groq import Groq
from agent.logger import logger
from config import GROQ_MODEL_NAME

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TAVILY_KEY = os.getenv("TAVILY_API_KEY")


def tavily_search(query: str):
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "include_answer": True,
        "max_results": 5
    }
    res = requests.post(url, json=payload)
    return res.json()


def research_company(company_name: str):
    query = f"{company_name} company overview products services competitors financials market share employee count global presence"
    data = tavily_search(query)

    return {
        "raw_answer": data.get("answer", ""),
        "sources": data.get("results", [])
    }


def _get_empty_sections(raw_text: str = "") -> dict:
    """Helper to return empty sections structure"""
    return {
        "overview": raw_text if raw_text else "",
        "products_services": "",
        "market_position": "",
        "competitors": "",
        "financial_snapshot": "",
        "key_contacts": "",
        "opportunities": "",
        "risks": "",
        "recommended_actions": ""
    }


def split_into_sections(raw_text: str) -> dict:
    """
    Split raw research text into structured sections using GROQ

    Args:
        raw_text: Raw text to split into sections

    Returns:
        Dict with structured sections
    """
    if not raw_text or not raw_text.strip():
        logger.warning("Empty raw_text provided to split_into_sections")
        return _get_empty_sections()

    prompt = f"""
                Break the following research text into structured sections.

                Required format:

                1. overview  
                - 4–6 full lines in paragraph form (no bullets)
                - Must include: what the company does, industry role, scale, impact
                - Include stats when possible, using uncertainty style e.g.
                    "Google employs approximately 180,000–190,000 people (varies by source)."

                2. products_services  
                    - Use bullet format EXACTLY like:
                    - Search & Ads: Google Search, Google Ads, YouTube Ads
                    - Cloud Services: Google Cloud Platform (GCP), Google Workspace
                    - Software & Platforms: Android, Chrome Browser, Maps, Gmail
                    - Hardware: Pixel devices, Nest smart-home products
                    - AI & ML: GROQ AI, Vertex AI

                3. market_position  
                - Paragraph only (2–4 lines)

                4. competitors  
                - Bullet list of competitor names only

                5. financial_snapshot  
                - 2–4 line paragraph including revenue strength, growth areas,
                    investment focus, and financial stability

                6. key_contacts  
                - 2–4 line description of typical executive roles (no names required)

                7. opportunities  
                - Bullet list of strategic opportunities

                8. risks  
                - Bullet list of risks

                9. recommended_actions  
                - Bullet list of recommended actions

                Return ONLY valid JSON with these keys.

                Raw research text:
                {raw_text}
            """

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000
        )

        if not response or not response.choices:
            logger.error("Empty response from GROQ in split_into_sections")
            return _get_empty_sections(raw_text)

        text = response.choices[0].message.content.strip()

        # Try to load JSON safely
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                cleaned = text.replace("```json", "").replace("```", "")
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in split_into_sections: {e}")
                return _get_empty_sections(raw_text)

    except Exception as e:
        logger.error(f"Error in split_into_sections: {e}")
        return _get_empty_sections(raw_text)


def complete_missing_sections(sections: dict) -> dict:
    """
    Complete or improve missing/weak sections using GROQ

    Args:
        sections: Dict of sections to improve

    Returns:
        Dict with completed sections
    """
    if not sections:
        logger.warning("Empty sections dict provided to complete_missing_sections")
        return _get_empty_sections()

    prompt = f"""
                    You are improving an account plan. Some sections may be empty or too short.
                    Rewrite and complete any weak sections while keeping:

                    - Overview: 4–6 full lines, paragraph form, including uncertain stats
                    - Products & Services: Style 1 bullet format (category → comma-separated items)
                    - Competitors: bullet list
                    - Financial Snapshot: strong 2–4 line paragraph
                    - Key Contacts: paragraph describing role types
                    - Opportunities, Risks, Actions: bullet lists

                    Return ONLY valid JSON.

                    Here are the sections to improve:
                    {sections}
                """

    try:
        response = groq_client.chat.completions.create(
            model=GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=2000
        )

        if not response or not response.choices:
            logger.error("Empty response from GROQ in complete_missing_sections")
            return sections

        text = response.choices[0].message.content.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                cleaned = text.replace("```json", "").replace("```", "")
                return json.loads(cleaned)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error in complete_missing_sections: {e}")
                return sections

    except Exception as e:
        logger.error(f"Error in complete_missing_sections: {e}")
        return sections
