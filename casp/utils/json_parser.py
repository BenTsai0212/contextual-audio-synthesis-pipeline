"""Robust JSON extraction from LLM responses.

LLMs often wrap JSON in markdown code blocks. This module strips that
and returns the parsed dict/list, raising ValueError on failure.
"""

import json
import re


def extract_json(text: str) -> dict | list:
    """Extract and parse JSON from an LLM response string.

    Handles:
    - Raw JSON
    - ```json ... ``` code blocks
    - ``` ... ``` code blocks (no language tag)
    - JSON embedded in surrounding prose
    """
    # Try direct parse first (fastest path)
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strip markdown code fences
    fence_pattern = re.compile(r"```(?:json)?\s*\n?(.*?)\n?```", re.DOTALL)
    match = fence_pattern.search(text)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find outermost { } or [ ] block
    for start_char, end_char in [('{', '}'), ('[', ']')]:
        start = text.find(start_char)
        end = text.rfind(end_char)
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

    raise ValueError(f"Could not extract valid JSON from LLM response. Preview: {text[:300]}")
