import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agent.tools import safe_json_parser, tavily_search, search_cache
from pydantic import BaseModel

class MockModel(BaseModel):
    name: str
    value: int

@pytest.mark.asyncio
async def test_safe_json_parser_clean_json():
    text = '{"name": "test", "value": 123}'
    result = await safe_json_parser(text, MockModel)
    assert result == {"name": "test", "value": 123}

@pytest.mark.asyncio
async def test_safe_json_parser_with_backticks():
    text = '```json\n{"name": "test", "value": 123}\n```'
    result = await safe_json_parser(text, MockModel)
    assert result == {"name": "test", "value": 123}

@pytest.mark.asyncio
async def test_safe_json_parser_malformed():
    text = "this is not json"
    with pytest.raises(ValueError, match="No JSON structure found in text"):
        await safe_json_parser(text, MockModel)

@pytest.mark.asyncio
async def test_tavily_cache_hit(mocker):
    search_cache.clear()
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_post.return_value.json.return_value = {"answer": "cached", "results": []}
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()

    await tavily_search("query1")
    await tavily_search("query1")
    
    assert mock_post.call_count == 1

@pytest.mark.asyncio
async def test_tavily_cache_miss(mocker):
    search_cache.clear()
    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_post.return_value.json.return_value = {"answer": "new", "results": []}
    mock_post.return_value.status_code = 200
    mock_post.return_value.raise_for_status = MagicMock()

    await tavily_search("query1")
    await tavily_search("query2")
    
    assert mock_post.call_count == 2
