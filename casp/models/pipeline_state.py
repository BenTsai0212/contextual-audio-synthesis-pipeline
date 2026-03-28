from typing import Annotated
from typing_extensions import TypedDict

from casp.models.ingestion import ContextPayload
from casp.models.dramatic import TensionMap, SensoryScript, SubtextReview
from casp.models.scene import Scene


def _replace(old, new):
    """Last-write-wins reducer for scalar fields."""
    return new if new is not None else old


def _increment(old, new):
    """Additive reducer for iteration counter."""
    return (old or 0) + (new or 0)


def _append(old, new):
    """List accumulation reducer for audit log."""
    return (old or []) + (new or [])


class PipelineState(TypedDict):
    # Immutable input — set once at graph entry
    context_payload: Annotated[ContextPayload, _replace]

    # Stage outputs — each node writes its own field
    tension_map: Annotated[TensionMap | None, _replace]
    sensory_script: Annotated[SensoryScript | None, _replace]
    subtext_review: Annotated[SubtextReview | None, _replace]

    # Loop control
    iteration: Annotated[int, _increment]
    max_iterations: Annotated[int, _replace]
    quality_approved: Annotated[bool, _replace]

    # Final output
    scenes: Annotated[list[Scene] | None, _replace]

    # Audit trail — accumulates across all iterations
    revision_log: Annotated[list[str], _append]
