import os
import json
import re
import time
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


# ---------------------------------------------------------------------------
# Cache Layer — Redis with silent in-memory fallback
# ---------------------------------------------------------------------------
class InMemoryCache:
    """Simple async-compatible TTL cache used when Redis is unavailable."""

    def __init__(self, maxsize: int = 200):
        self._store: Dict[str, str] = {}
        self._expiry: Dict[str, float] = {}
        self._maxsize = maxsize

    async def get(self, key: str) -> Optional[str]:
        if key in self._store:
            if time.monotonic() < self._expiry[key]:
                return self._store[key]
            # Expired — evict
            self._store.pop(key, None)
            self._expiry.pop(key, None)
        return None

    async def setex(self, key: str, ttl: int, value: str) -> None:
        # Evict oldest entry if at capacity
        if len(self._store) >= self._maxsize:
            oldest = next(iter(self._store))
            self._store.pop(oldest, None)
            self._expiry.pop(oldest, None)
        self._store[key] = value
        self._expiry[key] = time.monotonic() + ttl


def _build_cache_client():
    """Try to use Redis; fall back to in-memory cache if Redis is unreachable."""
    client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return client


# Shared cache client — replaced with InMemoryCache on first connection failure
redis_client = _build_cache_client()
_fallback_cache = InMemoryCache()
_using_redis = True  # mutable flag; flipped on first Redis failure


async def _cache_get(key: str) -> Optional[str]:
    global _using_redis
    if _using_redis:
        try:
            return await redis_client.get(key)
        except Exception:
            logger.warning(
                "Redis unavailable — switching to in-memory cache for this session."
            )
            _using_redis = False
    return await _fallback_cache.get(key)


async def _cache_setex(key: str, ttl: int, value: str) -> None:
    global _using_redis
    if _using_redis:
        try:
            await redis_client.setex(key, ttl, value)
            return
        except Exception:
            _using_redis = False
    await _fallback_cache.setex(key, ttl, value)

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
    locations: str = Field(default="")

def _sanitize_control_chars(text: str) -> str:
    """
    Remove or neutralize control characters that cause JSON parsing failures
    when LLMs embed raw newlines/tabs inside string values.

    - Keeps \t (0x09), \n (0x0a), \r (0x0d) but converts them to spaces so
      the JSON structural whitespace is preserved.
    - Strips all other C0 control characters (0x00-0x08, 0x0b, 0x0c, 0x0e-0x1f)
      and the DEL character (0x7f).
    """
    return re.sub(
        r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]',  # C0 controls (excl. \t \n \r)
        '',
        text
    )


async def safe_json_parser(text: str, model: Type[BaseModel]) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM output.

    Pipeline:
      1. Strip markdown fences.
      2. json.loads — fast path.
      3. Sanitize control characters, retry json.loads.
      4. Extract JSON via regex, retry json.loads.
      5. Validate with Pydantic model.
    """
    # 1. Strip markdown backticks
    cleaned = re.sub(r'```json\s*|\s*```', '', text).strip()

    data = None

    # 2. Fast path (using strict=False to allow raw newlines/control chars inside string values)
    try:
        data = json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass

    # 3. Control-character sanitization retry
    if data is None:
        sanitized = _sanitize_control_chars(cleaned)
        try:
            data = json.loads(sanitized, strict=False)
        except json.JSONDecodeError:
            pass

    # 4. Regex extraction + another sanitize round
    if data is None:
        target = _sanitize_control_chars(cleaned)
        match = re.search(r'\{.*\}', target, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(), strict=False)
            except json.JSONDecodeError as e:
                logger.error(f"Regex match found but failed to decode JSON: {e}. Match group: {match.group()}")
                raise ValueError("Could not parse JSON from LLM output")
        else:
            logger.error(f"No JSON structure found in text. Raw content: {text}")
            raise ValueError("No JSON structure found in text")

    # 5. Validate against Pydantic model
    try:
        validated = model(**data)
        return validated.model_dump()
    except ValidationError as e:
        logger.error(f"Pydantic validation failed: {e}")
        return data  # Return raw dict if validation fails but format is correct

async def tavily_search(query: str):
    cache_key = f"tavily:{hashlib.md5(query.encode()).hexdigest()}"

    # Try cache (Redis or in-memory fallback)
    cached = await _cache_get(cache_key)
    if cached:
        logger.info(f"Cache hit for query: {query[:60]}")
        return json.loads(cached)

    url = "https://api.tavily.com/search"
    payload = {
        "api_key": settings.TAVILY_API_KEY,
        "query": query,
        "include_answer": True,
        "include_images": True,
        "max_results": settings.TAVILY_MAX_RESULTS,
    }

    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(url, json=payload, timeout=20.0)
            res.raise_for_status()
            data = res.json()

            # Cache for 1 hour (3600 seconds)
            await _cache_setex(cache_key, 3600, json.dumps(data))

            return data
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"answer": "", "results": [], "images": []}

async def research_company(company_name: str):
    query = f"{company_name} company overview products services competitors financials market share employee count locations main branch sub branches global presence"
    data = await tavily_search(query)

    return {
        "raw_answer": data.get("answer", ""),
        "sources": data.get("results", []),
        "images": data.get("images", [])
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
        "recommended_actions": "",
        "locations": ""
    }

async def split_into_sections(raw_text: str, company_name: str) -> dict:
    if not raw_text or not raw_text.strip():
        return _get_empty_sections()

    prompt = f"""
    Break the following research text into structured sections for {company_name}.
    Return ONLY valid JSON with keys: overview, products_services, market_position, competitors, financial_snapshot, key_contacts, opportunities, risks, recommended_actions, locations.
    For locations, include details about the main branch and any sub-branches or global presence.
    CRITICAL: Every value in the JSON MUST be a comprehensive, detailed string (at least 3-5 bullet points or 2 detailed paragraphs per section). Use markdown bullet points for lists. Do NOT return nested objects or dictionaries.
    
    Raw text:
    {raw_text}
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2500
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
    Based on the research for {company_name}, perform a deep strategic analysis to fill in any gaps.
    Return ONLY valid JSON with keys: overview, products_services, market_position, competitors, financial_snapshot, key_contacts, opportunities, risks, recommended_actions, locations.
    For locations, include details about the main branch and any sub-branches or global presence.
    CRITICAL: Every value in the JSON MUST be a comprehensive, detailed string (at least 3-5 bullet points or 2 detailed paragraphs per section). Provide specific names, data points, and strategic insights where possible. Do NOT return nested objects or dictionaries.
    
    Focus on strategic inference, market trends, and missing context.
    
    Raw text:
    {raw_text}
    """
    
    try:
        response = groq_client.chat.completions.create(
            model=settings.GROQ_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=2500
        )
        text = response.choices[0].message.content
        parsed = await safe_json_parser(text, PartialPlan)
        return parsed
    except Exception as e:
        logger.error(f"Error in complete_missing_sections: {e}")
        return _get_empty_sections()
