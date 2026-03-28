"""Integration test: full LangGraph Dramatic Processing Engine run.

Uses CASP_TEST_MODE (set in conftest.py) so no real API calls are made.
Validates that the graph runs to completion and produces valid Scene output.
"""

import json
from pathlib import Path

import pytest

from casp.dramatic.graph import build_dramatic_graph
from casp.models.ingestion import ContextPayload
from casp.models.scene import Scene

FIXTURES = Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_payload() -> ContextPayload:
    data = json.loads((FIXTURES / "sample_context_payload.json").read_text())
    return ContextPayload.model_validate(data)


def test_graph_runs_to_completion(sample_payload):
    """The graph should invoke successfully and return a non-empty scenes list."""
    graph = build_dramatic_graph()

    initial_state = {
        "context_payload": sample_payload,
        "tension_map": None,
        "sensory_script": None,
        "subtext_review": None,
        "iteration": 0,
        "max_iterations": 3,
        "quality_approved": False,
        "scenes": None,
        "revision_log": [],
    }

    final_state = graph.invoke(initial_state)

    assert final_state["scenes"] is not None
    assert len(final_state["scenes"]) > 0


def test_graph_produces_valid_scenes(sample_payload):
    """All scenes in the output must validate against the Scene schema."""
    graph = build_dramatic_graph()

    final_state = graph.invoke({
        "context_payload": sample_payload,
        "tension_map": None,
        "sensory_script": None,
        "subtext_review": None,
        "iteration": 0,
        "max_iterations": 3,
        "quality_approved": False,
        "scenes": None,
        "revision_log": [],
    })

    for scene in final_state["scenes"]:
        assert isinstance(scene, Scene)
        assert scene.scene_id
        assert len(scene.audio_layers) > 0


def test_graph_accumulates_revision_log(sample_payload):
    """The revision_log should have at least one entry from each node."""
    graph = build_dramatic_graph()

    final_state = graph.invoke({
        "context_payload": sample_payload,
        "tension_map": None,
        "sensory_script": None,
        "subtext_review": None,
        "iteration": 0,
        "max_iterations": 1,  # Force single pass
        "quality_approved": False,
        "scenes": None,
        "revision_log": [],
    })

    log = final_state["revision_log"]
    assert any("Tension Architect" in entry for entry in log)
    assert any("Sensory Renderer" in entry for entry in log)
    assert any("Subtext Editor" in entry for entry in log)
    assert any("Audio Tagger" in entry for entry in log)


def test_graph_exits_loop_at_max_iterations(sample_payload):
    """Even if quality is not approved, graph must stop at max_iterations."""
    import json
    from unittest.mock import patch

    # Force the subtext editor to always reject
    reject_review = {
        "approved": False,
        "quality_score": 4.0,
        "overall_notes": "Forced rejection for test.",
        "issues": []
    }

    with patch("casp.dramatic.agents.subtext_editor.call_claude", return_value=json.dumps(reject_review)):
        graph = build_dramatic_graph()
        final_state = graph.invoke({
            "context_payload": sample_payload,
            "tension_map": None,
            "sensory_script": None,
            "subtext_review": None,
            "iteration": 0,
            "max_iterations": 2,
            "quality_approved": False,
            "scenes": None,
            "revision_log": [],
        })

    # Should still produce scenes despite rejection (max_iterations forces exit)
    assert final_state["scenes"] is not None
    # iteration should be >= max_iterations
    assert final_state["iteration"] >= 2
