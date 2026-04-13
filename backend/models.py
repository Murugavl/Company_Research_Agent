from pydantic import BaseModel, Field
from typing import List, Optional

class AccountPlanModel(BaseModel):
    company_name: str
    overview: str = Field(..., description="4–6 lines paragraph overview")
    products_services: str = Field(..., description="Bullet list of products and services")
    market_position: str = Field(..., description="2–4 lines paragraph on market position")
    competitors: str = Field(..., description="Bullet list of competitor names")
    financial_snapshot: str = Field(..., description="2–4 lines paragraph on financials")
    key_contacts: str = Field(..., description="Description of typical executive roles")
    opportunities: str = Field(..., description="Bullet list of strategic opportunities")
    risks: str = Field(..., description="Bullet list of risks")
    recommended_actions: str = Field(..., description="Bullet list of recommended actions")

class ResearchResult(BaseModel):
    raw_answer: str
    sources: List[dict]
