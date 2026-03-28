"""Shared Anthropic client factory and call helper."""

import json
import os
from pathlib import Path

import anthropic

from casp.config import settings
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_client: anthropic.Anthropic | None = None


def get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def call_claude(
    system_prompt: str,
    user_content: str,
    model: str | None = None,
    max_tokens: int = 4096,
) -> str:
    """Call Claude and return the response text.

    In CASP_TEST_MODE, reads from tests/fixtures/<md5_hash>.json instead
    of making real API calls so that unit/integration tests are free.
    """
    if settings.test_mode or os.environ.get("CASP_TEST_MODE") == "1":
        return _fixture_response(system_prompt, user_content)

    effective_model = model or settings.default_model
    logger.debug("Calling Claude model=%s max_tokens=%d", effective_model, max_tokens)

    client = get_client()
    response = client.messages.create(
        model=effective_model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_content}],
    )
    return response.content[0].text


def _fixture_response(system_prompt: str, user_content: str) -> str:
    """Return a canned fixture response based on the agent identity line.

    Each agent prompt begins with 'You are the <AgentName>'. We match on the
    first line to avoid false positives from cross-mentions in prompt bodies.
    """
    first_line = system_prompt.strip().split("\n")[0].lower()
    fixtures_dir = Path(__file__).parent.parent.parent / "tests" / "fixtures"

    if "tension architect" in first_line:
        fixture = fixtures_dir / "fixture_tension_map.json"
    elif "sensory renderer" in first_line:
        fixture = fixtures_dir / "fixture_sensory_script.json"
    elif "subtext editor" in first_line:
        fixture = fixtures_dir / "fixture_subtext_review.json"
    else:
        fixture = fixtures_dir / "fixture_context_payload.json"

    if fixture.exists():
        return fixture.read_text(encoding="utf-8")

    raise FileNotFoundError(
        f"Test fixture not found: {fixture}. "
        "Run tests from the project root or create the fixture file."
    )
