import os
import requests
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
    """
    Fetch raw research data from Tavily.
    Only raw text + sources are returned.
    """
    query = f"{company_name} company overview products services competitors financials market share employee count global presence"
    data = tavily_search(query)

    return {
        "raw_answer": data.get("answer", ""),
        "sources": data.get("results", [])
    }


def split_into_sections(raw_text: str) -> dict:
    """
    Ask Gemini to split raw research text into structured sections.
    Overview must be 4–6 detailed lines.
    Products & Services must follow Category → Items format.
    Stats must include uncertainty when conflicting.
    """

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
     - AI & ML: Gemini AI, Vertex AI

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

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    text = response.text.strip()

    # Try to load JSON safely
    import json
    try:
        return json.loads(text)
    except:
        try:
            cleaned = text.replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except:
            # Fallback in worst case
            return {
                "overview": raw_text,
                "products_services": "",
                "market_position": "",
                "competitors": "",
                "financial_snapshot": "",
                "key_contacts": "",
                "opportunities": "",
                "risks": "",
                "recommended_actions": ""
            }


def complete_missing_sections(sections: dict) -> dict:
    """
    Improve or fill weak/empty sections using Gemini.
    Ensures every section is meaningful and complete.
    """

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

    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)

    text = response.text.strip()

    import json
    try:
        return json.loads(text)
    except:
        try:
            cleaned = text.replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except:
            return sections
