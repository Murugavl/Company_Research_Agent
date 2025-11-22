import os
import requests
from typing import Dict, Any

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
TAVILY_KEY = os.getenv("TAVILY_API_KEY")


# calling tavily search api
def tavily_search(query: str) -> Any:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "include_answer": True,
        "max_results": 5,
    }
    res = requests.post(url, json=payload)
    return res.json()


# convertion of tavily result into a structured research output
def research_company(company_name: str) -> Dict[str, Any]:
    q = f"{company_name} company overview products services competitors financials market position"
    data = tavily_search(q)

    answer = data.get("answer", "")
    sources = data.get("results", [])

    # basic structure for research data
    return {
        "raw_answer": answer,
        "sources": sources,
    }


# take raw research text and turn it into structured plan sections
def split_into_sections(raw_text: str) -> Dict[str, str]:
    prompt = f"""
Split this company research into these sections:

- overview
- products_services
- market_position
- competitors
- financial_snapshot
- key_contacts
- opportunities
- risks
- recommended_actions

For list-type fields (competitors, opportunities, risks, recommended_actions),
use markdown bullet points (- ...), each on its own line.

Return ONLY a JSON object with these keys.

Raw text:
{raw_text}
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    res = model.generate_content(prompt)
    text = res.text.strip()

    try:
        import json
        return json.loads(text)
    except:
        try:
            fixed = text.replace("```json", "").replace("```", "")
            return json.loads(fixed)
        except:
            return {
                "overview": raw_text,
                "products_services": "",
                "market_position": "",
                "competitors": "",
                "financial_snapshot": "",
                "key_contacts": "",
                "opportunities": "",
                "risks": "",
                "recommended_actions": "",
            }


# fill missing or weak sections using gemini
def complete_missing_sections(sections: Dict[str, str]) -> Dict[str, str]:
    prompt = f"""
Given the partially filled company summary below, improve and complete any weak or empty sections.
Keep the writing concise and business-oriented.
Use bullet points where it makes sense.

Sections:
{sections}

Return ONLY valid JSON with the same keys.
"""
    model = genai.GenerativeModel("gemini-2.0-flash")
    res = model.generate_content(prompt)
    text = res.text.strip()

    try:
        import json
        return json.loads(text)
    except:
        try:
            cleaned = text.replace("```json", "").replace("```", "")
            return json.loads(cleaned)
        except:
            return sections
