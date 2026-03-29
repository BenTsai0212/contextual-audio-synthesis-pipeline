"""Unit tests for the Subtext Editor agent quality gate logic."""

import json
from pathlib import Path
from unittest.mock import patch

from casp.dramatic.agents.subtext_editor import subtext_editor_node, QUALITY_THRESHOLD
from casp.models.dramatic import SensoryScript, SubtextReview
from casp.models.pipeline_state import PipelineState

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _make_state(score: float, approved: bool) -> PipelineState:
    sensory_data = json.loads((FIXTURES / "fixture_sensory_script.json").read_text(encoding="utf-8"))
    review_data = json.loads((FIXTURES / "fixture_subtext_review.json").read_text(encoding="utf-8"))
    # Override score and approved for testing
    review_data["quality_score"] = score
    review_data["approved"] = approved

    return {
        "context_payload": None,
        "tension_map": None,
        "sensory_script": SensoryScript.model_validate(sensory_data),
        "subtext_review": None,
        "iteration": 1,
        "max_iterations": 3,
        "quality_approved": False,
        "scenes": None,
        "revision_log": [],
    }


def test_quality_gate_passes_when_score_above_threshold():
    state = _make_state(8.2, True)
    # call_claude is intercepted by CASP_TEST_MODE (set in conftest.py)
    result = subtext_editor_node(state)
    assert result["quality_approved"] is True


def test_quality_gate_fails_when_score_below_threshold():
    """Simulate a low-score fixture by patching call_claude to return a low score."""
    low_score_review = {
        "approved": False,
        "quality_score": 5.0,
        "overall_notes": "Too many AI-sounding phrases.",
        "issues": []
    }

    with patch("casp.dramatic.agents.subtext_editor.call_claude", return_value=json.dumps(low_score_review)):
        state = _make_state(5.0, False)
        result = subtext_editor_node(state)
        assert result["quality_approved"] is False


def test_revision_log_is_populated():
    state = _make_state(8.2, True)
    result = subtext_editor_node(state)
    assert len(result["revision_log"]) == 1
    assert "Subtext Editor" in result["revision_log"][0]
