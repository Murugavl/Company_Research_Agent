from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class AccountPlanModel(BaseModel):
    company_name: str
    overview: str = Field(default="", description="4–6 lines paragraph overview")
    products_services: str = Field(default="", description="Bullet list of products and services")
    market_position: str = Field(default="", description="2–4 lines paragraph on market position")
    competitors: str = Field(default="", description="Bullet list of competitor names")
    financial_snapshot: str = Field(default="", description="2–4 lines paragraph on financials")
    key_contacts: str = Field(default="", description="Description of typical executive roles")
    opportunities: str = Field(default="", description="Bullet list of strategic opportunities")
    risks: str = Field(default="", description="Bullet list of risks")
    recommended_actions: str = Field(default="", description="Bullet list of recommended_actions")
    locations: str = Field(default="", description="Information about main branch, sub-branches and global locations")
    company_images: List[str] = Field(default_factory=list, description="Images related to the company")
    sources: List[dict] = Field(default_factory=list, description="Source citations with title and url")
    extra_sections: Dict[str, str] = Field(default_factory=dict, description="Custom sections dynamic dictionary")

class ResearchResult(BaseModel):
    raw_answer: str
    sources: List[dict]
