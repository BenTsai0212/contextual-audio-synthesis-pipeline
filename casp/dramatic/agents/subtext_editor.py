"""Subtext Editor Agent Node — Quality Gate.

Reviews the SensoryScript for authenticity, subtext depth, and naturalness.
Sets quality_approved=True when quality_score >= 7.5.
"""

import json
from pathlib import Path

from casp.models.dramatic import SensoryScript, SubtextReview
from casp.models.pipeline_state import PipelineState
from casp.utils.json_parser import extract_json
from casp.utils.llm import call_claude
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_PROMPT = (Path(__file__).parent.parent / "prompts" / "subtext_editor.txt").read_text(
    encoding="utf-8"
)

QUALITY_THRESHOLD = 7.5


def _build_user_content(sensory_script: SensoryScript) -> str:
    return json.dumps(sensory_script.model_dump(), ensure_ascii=False, indent=2)


def subtext_editor_node(state: PipelineState) -> dict:
    sensory_script = state["sensory_script"]
    iteration = state.get("iteration", 1)

    logger.info("Subtext Editor — reviewing %d lines (iteration %d)", len(sensory_script.lines), iteration)

    raw = call_claude(
        system_prompt=_PROMPT,
        user_content=_build_user_content(sensory_script),
    )

    review = SubtextReview.model_validate(extract_json(raw))

    # Quality gate
    quality_approved = review.quality_score >= QUALITY_THRESHOLD
    review.approved = quality_approved  # Enforce consistency with our threshold

    log_entry = (
        f"[iter {iteration}] Subtext Editor: score={review.quality_score:.1f} "
        f"approved={quality_approved} issues={len(review.issues)}"
    )
    logger.info(log_entry)

    if quality_approved:
        logger.info("Quality gate PASSED — proceeding to audio tagging")
    else:
        logger.info(
            "Quality gate FAILED — routing back to Tension Architect. Notes: %s",
            review.overall_notes,
        )

    return {
        "subtext_review": review,
        "quality_approved": quality_approved,
        "revision_log": [log_entry],
    }
