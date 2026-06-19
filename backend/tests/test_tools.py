import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from agent.tools import safe_json_parser, tavily_search
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
async def test_safe_json_parser_raw_control_chars():
    # Test JSON string with a raw newline inside the string value
    text = '{\n  "name": "test\nline2",\n  "value": 123\n}'
    result = await safe_json_parser(text, MockModel)
    assert result == {"name": "test\nline2", "value": 123}

@pytest.mark.asyncio
async def test_tavily_cache_hit(mocker, mock_redis):
    """When Redis has a cached result, Tavily API should NOT be called."""
    import json
    cached_data = {"answer": "cached", "results": [], "images": []}
    mock_redis.get.return_value = json.dumps(cached_data)

    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)

    result = await tavily_search("query1")

    assert result == cached_data
    mock_post.assert_not_called()

@pytest.mark.asyncio
async def test_tavily_cache_miss(mocker, mock_redis):
    """When Redis has no cache, Tavily API should be called and result cached."""
    mock_redis.get.return_value = None  # No cache

    # httpx Response methods (json, raise_for_status) are synchronous
    mock_response = MagicMock()
    mock_response.json.return_value = {"answer": "new", "results": [], "images": []}
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_post = mocker.patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    mock_post.return_value = mock_response

    result = await tavily_search("query2")

    assert mock_post.call_count == 1
    assert result["answer"] == "new"
    mock_redis.setex.assert_called_once()
