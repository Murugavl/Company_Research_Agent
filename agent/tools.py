import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# calling tavily search api
def tavily_search(query: str) -> Any:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_KEY,
        "query": query,
        "include_answer": True,
        "max_results": 5
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
        "sources": sources
    }
