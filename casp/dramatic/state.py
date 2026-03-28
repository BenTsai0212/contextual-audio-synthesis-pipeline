"""LangGraph routing logic for the Dramatic Processing Engine."""

from typing import Literal

from casp.models.pipeline_state import PipelineState


def route_after_editor(state: PipelineState) -> Literal["audio_tagger", "tension_architect"]:
    """Conditional edge: loop back or proceed to audio tagging."""
    iteration = state.get("iteration", 1)
    max_iterations = state.get("max_iterations", 3)

    if state.get("quality_approved") or iteration >= max_iterations:
        return "audio_tagger"
    return "tension_architect"
