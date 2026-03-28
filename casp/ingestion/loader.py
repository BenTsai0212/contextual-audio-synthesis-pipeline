"""Data Ingestion Loader.

Supports loading raw content from:
  - Local text files (.txt, .md)
  - Local JSON files (ContextPayload schema)
  - HTTP/HTTPS URLs
  - RSS feeds
  - Raw text strings (RAW_TEXT type)
"""

import json
from pathlib import Path

import httpx

from casp.models.ingestion import ContextPayload, InputType, RawInput
from casp.utils.logging import get_logger

logger = get_logger(__name__)


def detect_input_type(source: str) -> InputType:
    """Auto-detect input type from the source string."""
    if source.startswith(("http://", "https://")):
        # Heuristic: if it ends with .xml or contains 'rss' or 'feed'
        lower = source.lower()
        if any(k in lower for k in ("rss", "feed", "atom", ".xml")):
            return InputType.RSS
        return InputType.URL
    path = Path(source)
    if path.suffix.lower() == ".json":
        return InputType.JSON
    return InputType.TEXT_FILE


def load_raw_input(source: str, input_type: InputType | None = None) -> RawInput:
    """Load content from source and return a RawInput object."""
    if input_type is None:
        input_type = detect_input_type(source)

    logger.debug("Loading input type=%s source=%s", input_type, source[:80])

    if input_type == InputType.JSON:
        content = Path(source).read_text(encoding="utf-8")
        return RawInput(input_type=input_type, content=content, source_uri=source)

    if input_type == InputType.TEXT_FILE:
        content = Path(source).read_text(encoding="utf-8")
        return RawInput(input_type=input_type, content=content, source_uri=source)

    if input_type == InputType.URL:
        response = httpx.get(source, follow_redirects=True, timeout=15.0)
        response.raise_for_status()
        return RawInput(input_type=input_type, content=response.text, source_uri=source)

    if input_type == InputType.RSS:
        import feedparser
        feed = feedparser.parse(source)
        # Concatenate all entry summaries
        parts = []
        for entry in feed.entries[:10]:  # Cap at 10 items
            title = entry.get("title", "")
            summary = entry.get("summary", entry.get("description", ""))
            parts.append(f"## {title}\n{summary}")
        content = "\n\n".join(parts)
        return RawInput(input_type=input_type, content=content, source_uri=source)

    if input_type == InputType.RAW_TEXT:
        return RawInput(input_type=input_type, content=source)

    raise ValueError(f"Unsupported input type: {input_type}")


def load_context_payload(source: str, input_type: InputType | None = None) -> ContextPayload | RawInput:
    """Attempt to load directly as a ContextPayload JSON.

    If the source is a JSON file containing a ContextPayload schema, return it
    directly (bypassing the denoiser step). Otherwise, return a RawInput for
    processing by the denoiser.
    """
    raw = load_raw_input(source, input_type)

    if raw.input_type == InputType.JSON:
        try:
            data = json.loads(raw.content)
            if "core_facts" in data:
                return ContextPayload.model_validate(data)
        except Exception:
            pass  # Fall through to return as RawInput for denoising

    return raw
