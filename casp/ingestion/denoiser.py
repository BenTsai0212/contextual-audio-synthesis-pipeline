"""Denoiser — Stage 1 LLM processing.

Takes a RawInput and produces a clean ContextPayload by:
- Filtering ads, navigation text, and irrelevant content
- Extracting core facts (Facts) and pivot points
- Assigning emotional weights
"""

import json
import uuid

from casp.models.ingestion import ContextPayload, RawInput
from casp.utils.json_parser import extract_json
from casp.utils.llm import call_claude
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_DENOISER_PROMPT = """\
You are a content extraction and denoising specialist.

Your task: extract the essential narrative material from raw text and identify the core facts, turning points, and emotional anchors.

## Instructions

1. **Remove noise**: Ignore ads, navigation menus, cookie notices, social media share buttons, author bio boilerplate, and any content unrelated to the main narrative.

2. **Extract core facts**: Identify 5–12 discrete factual statements that form the backbone of the story. Each fact should:
   - Be self-contained and verifiable
   - Carry emotional or narrative significance
   - Be marked as a `pivot_point` if it represents a turning point in the story

3. **Assign emotional weight** (0.0–1.0):
   - 0.0 = neutral/administrative fact
   - 0.5 = moderately significant
   - 1.0 = highly emotionally charged or shocking

4. **Determine domain**: Classify the content as "psychology", "history", "crime", "science", "personal_narrative", or "current_events".

## Output Format

Respond ONLY with a valid JSON object:

```json
{
  "payload_id": "<uuid>",
  "title": "<concise title for this episode, max 60 chars>",
  "domain": "<domain>",
  "raw_summary": "<2-3 sentence neutral summary of the source material>",
  "word_count_original": <integer>,
  "core_facts": [
    {
      "fact_id": "f01",
      "statement": "<clear, concise factual statement>",
      "emotional_weight": <0.0-1.0>,
      "pivot_point": <true|false>
    }
  ],
  "metadata": {}
}
```
"""


def denoise(raw_input: RawInput, title_hint: str | None = None) -> ContextPayload:
    """Process a RawInput through the LLM denoiser and return a ContextPayload."""
    logger.info("Denoising input (type=%s, length=%d chars)", raw_input.input_type, len(raw_input.content))

    user_content = raw_input.content
    if title_hint:
        user_content = f"[Title hint: {title_hint}]\n\n{user_content}"

    raw = call_claude(
        system_prompt=_DENOISER_PROMPT,
        user_content=user_content,
        max_tokens=2048,
    )

    data = extract_json(raw)

    # Ensure a payload_id exists
    if not data.get("payload_id"):
        data["payload_id"] = str(uuid.uuid4())

    payload = ContextPayload.model_validate(data)
    logger.info("Denoiser extracted %d facts from '%s'", len(payload.core_facts), payload.title)
    return payload
