from unittest.mock import AsyncMock

import pytest

from agent.agent_core import _friendly_research_error, generate_agent_reply_stream


class GroqAPIError(Exception):
    def __init__(self, status_code):
        super().__init__("upstream error")
        self.status_code = status_code


def test_unavailable_model_error_is_not_reported_as_rate_limit():
    message = _friendly_research_error(GroqAPIError(404))

    assert "model is unavailable" in message
    assert "rate limit" not in message.lower()


def test_summary_rate_limit_says_report_is_available():
    message = _friendly_research_error(GroqAPIError(429), summary_only=True)

    assert "report is available" in message
    assert "rate limit" in message.lower()


@pytest.mark.asyncio
async def test_stream_reports_unavailable_model_as_an_error(mocker):
    mocker.patch(
        "agent.nodes.node_normalize",
        new=AsyncMock(side_effect=GroqAPIError(404)),
    )

    events = [
        event
        async for event in generate_agent_reply_stream(
            user_message="Research Example Co",
            company_name="Example Co",
            current_plan=None,
            chat_history=[],
            session_id="test-session",
        )
    ]

    assert len(events) == 1
    assert events[0]["type"] == "error"
    assert "model is unavailable" in events[0]["message"]
