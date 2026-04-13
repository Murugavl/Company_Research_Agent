import os
import json
import re
import asyncio
import hashlib
import httpx
from typing import Dict, Any, Optional, Type
from pydantic import BaseModel, ValidationError, Field
import redis.asyncio as aioredis
from groq import Groq
from agent.logger import logger
from config import settings
from models import AccountPlanModel

# Initialize Groq client once at module level
groq_client = Groq(api_key=settings.GROQ_API_KEY)

# Redis client for search result caching
redis_client = aioredis.from_url(
    settings.REDIS_URL,
    decode_responses=True
)

class PartialPlan(BaseModel):
    """Pydantic model for structured research sections with defaults."""
    overview: str = Field(default="")
    products_services: str = Field(default="")
    market_position: str = Field(default="")
    competitors: str = Field(default="")
    financial_snapshot: str = Field(default="")
    key_contacts: str = Field(default="")
    opportunities: str = Field(default="")
    risks: str = Field(default="")
    recommended_actions: str = Field(default="")

async def safe_json_parser(text: str, model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM output, stripping markdown and using regex fallback.
    Validates against a Pydantic model.
    """
    # 1. Strip markdown backticks
    cleaned = re.sub(r'```json\s*|\s*```', '', text).strip()
    
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # 2. Fallback to regex search for anything between braces
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
            except json.JSONDecodeError as e:
                logger.error(f"Regex match found but failed to decode JSON: {e}")
                raise ValueError("Could not parse JSON from LLM output")
        else:
            logger.error("No JSON structure found in text")
            raise ValueError("No JSON structure found in text")

    # 3. Validate against Pydantic model
    try:
        validated = model(**data)
        return validated.model_dump()
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        return data  # Fallback to raw data if validation fails but format is correct

async def tavily_search(query: str):
    cache_key = f"tavily:{hashlib.md5(query.encode()).hexdigest()}"
    
    try:
        cached = await redis_client.get(cache_key)
        if cached:
            logger.info(f"Using cached result for query: {query}")
            return json.loads(cached)
    except Exception as e:
        logger.warning(f"Cache lookup failed: {e}")

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "include_answer": True,
        "max_results": settings.TAVILY_MAX_RESULTS
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=20.0)
            res.raise_for_status()
            data = res.json()
            
            # Cache for 1 hour (3600 seconds)
            try:
                await redis_client.setex(cache_key, 3600, json.dumps(data))
            except Exception as e:
                logger.warning(f"Cache save failed: {e}")
                
            return data
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"answer": "", "results": []}

async def research_company(company_name: str):
    query = f"{company_name} company overview products services competitors financials market share employee count global presence"
    data = await tavily_search(query)

    return {
        "raw_answer": data.get("answer", ""),
        "sources": data.get("results", [])
    }

def _get_empty_sections(raw_text: str = "") -> dict:
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

async def split_into_sections(raw_text: str, company_name: str) -> dict:
    if not raw_text or not raw_text.strip():
        return _get_empty_sections()

    prompt = f"""
    Break the following research text into structured sections for {company_name}.
    Return ONLY valid JSON with keys: overview, products_services, market_position, competitors, financial_snapshot, key_contacts, opportunities, risks, recommended_actions.
    
    Focus on structuring existing information.
    
    Raw text:
    {raw_text}
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        text = response.choices[0].message.content
        parsed = await safe_json_parser(text, PartialPlan)
        return parsed
    except Exception as e:
        logger.error(f"Error in split_into_sections: {e}")
        return _get_empty_sections(raw_text)

async def complete_missing_sections(raw_text: str, company_name: str) -> dict:
    """Independently extract and enrich sections to be run concurrently with split."""
    prompt = f"""
    Based on the research for {company_name}, fill in any strategic gaps.
    Return ONLY valid JSON with keys: overview, products_services, market_position, competitors, financial_snapshot, key_contacts, opportunities, risks, recommended_actions.
    
    Focus on strategic inference and missing context.
    
    Raw text:
    {raw_text}
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        text = response.choices[0].message.content
        parsed = await safe_json_parser(text, PartialPlan)
        return parsed
    except Exception as e:
        logger.error(f"Error in complete_missing_sections: {e}")
        return _get_empty_sections()
