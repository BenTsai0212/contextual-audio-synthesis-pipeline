"""Sensory Renderer Agent Node.

Converts abstract prose from the TensionMap into physically grounded,
sensory-rich dialogue lines with ambient sound tags.
"""

import json
from pathlib import Path

from casp.models.dramatic import TensionMap, SensoryScript
from casp.models.pipeline_state import PipelineState
from casp.utils.json_parser import extract_json
from casp.utils.llm import call_claude
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_PROMPT = (Path(__file__).parent.parent / "prompts" / "sensory_renderer.txt").read_text(
    encoding="utf-8"
)


def _build_user_content(tension_map: TensionMap) -> str:
    return json.dumps(tension_map.model_dump(), ensure_ascii=False, indent=2)


def sensory_renderer_node(state: PipelineState) -> dict:
    tension_map = state["tension_map"]
    iteration = state.get("iteration", 1)

    logger.info("Sensory Renderer — iteration %d, %d acts to process", iteration, len(tension_map.acts))

    raw = call_claude(
        system_prompt=_PROMPT,
        user_content=_build_user_content(tension_map),
    )

    sensory_script = SensoryScript.model_validate(extract_json(raw))
    log_entry = f"[iter {iteration}] Sensory Renderer: {len(sensory_script.lines)} lines, {len(sensory_script.sfx_markers)} SFX markers"
    logger.debug(log_entry)

    return {
        "sensory_script": sensory_script,
        "revision_log": [log_entry],
    }
