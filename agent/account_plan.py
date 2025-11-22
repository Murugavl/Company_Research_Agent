from dataclasses import dataclass, asdict
from typing import Dict, Any

# structure for storing the account plan
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

    # get plan as dict so UI can display easily
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    # quick helper to start an empty plan
    @staticmethod
    def empty(company_name: str) -> "AccountPlan":
        return AccountPlan(company_name = company_name)
