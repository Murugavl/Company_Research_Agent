from typing import Dict, Any

def mock_research_company(company_name: str) -> Dict[str, Any]:
    """
    This is a temporary mock research tool.
    It returns placeholder details for any company.
    You will later replace it with real web research.
    """
    return {
        "overview": f"{company_name} is a well-known company in its industry. This overview is generated from mock data.",
        "products_services": f"{company_name} offers various products and services depending on user context. (mock data)",
        "market_position": f"{company_name} has a notable position in the global market. (mock data)",
        "competitors": "Competitors may include several companies in the same industry. (mock data)",
        "financial_snapshot": "Financial data is unavailable in mock mode. (mock data)",
        "key_contacts": "Key people include CEO, CTO, and other leadership roles. (mock data)",
        "opportunities": "There are opportunities for growth in AI, cloud, and digital transformation. (mock data)",
        "risks": "Risks include competition, market fluctuations, and regulatory challenges. (mock data)",
        "recommended_actions": "Recommended actions include market research, customer engagement, and innovation investment. (mock data)"
    }


