from dataclasses import dataclass, asdict
from typing import Dict, Any

@dataclass
class AccountPlan:
    company_name: str
    overview: str = ""
    products_services: str = ""
    market_position: str = ""
    competitors: str = ""
    financial_snapshot: str = ""
    key_contacts: str = ""
    opportunities: str = ""
    risks: str = ""
    recommended_actions: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @staticmethod
    def empty(company_name: str) -> "AccountPlan":
        return AccountPlan(company_name = company_name)
