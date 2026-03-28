"""Tension Architect Agent Node.

Generates a 5-act TensionMap from the ContextPayload.
On subsequent iterations, incorporates revision_notes from the Subtext Editor.
"""

import json
from pathlib import Path

from casp.models.ingestion import ContextPayload
from casp.models.dramatic import TensionMap
from casp.models.pipeline_state import PipelineState
from casp.utils.json_parser import extract_json
from casp.utils.llm import call_claude
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_PROMPT = (Path(__file__).parent.parent / "prompts" / "tension_architect.txt").read_text(
    encoding="utf-8"
)


def _build_user_content(payload: ContextPayload, revision_notes: str) -> str:
    data = {
        "payload_id": payload.payload_id,
        "title": payload.title,
        "domain": payload.domain,
        "raw_summary": payload.raw_summary,
        "core_facts": [f.model_dump() for f in payload.core_facts],
    }
    if revision_notes:
        data["revision_notes"] = revision_notes
    return json.dumps(data, ensure_ascii=False, indent=2)


def tension_architect_node(state: PipelineState) -> dict:
    payload = state["context_payload"]
    iteration = state.get("iteration", 0)

    # Carry forward revision notes from previous editor pass
    revision_notes = ""
    if state.get("subtext_review") and not state.get("quality_approved"):
        revision_notes = state["subtext_review"].overall_notes

    logger.info("Tension Architect — iteration %d, payload '%s'", iteration + 1, payload.title)

    raw = call_claude(
        system_prompt=_PROMPT,
        user_content=_build_user_content(payload, revision_notes),
    )

    tension_map = TensionMap.model_validate(extract_json(raw))
    log_entry = f"[iter {iteration + 1}] Tension Architect: generated {len(tension_map.acts)} acts, peak at minute {tension_map.overall_peak_minute}"
    logger.debug(log_entry)

    return {
        "tension_map": tension_map,
        "iteration": 1,  # additive reducer — increments the counter
        "revision_log": [log_entry],
    }
