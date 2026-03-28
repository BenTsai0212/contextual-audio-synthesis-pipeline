"""Unit tests for Pydantic data models."""

import json
from pathlib import Path

import pytest

from casp.models.ingestion import ContextPayload, CoreFact
from casp.models.dramatic import TensionMap, SensoryScript, SubtextReview
from casp.models.scene import Scene, EmotionTag, VibeParameters

FIXTURES = Path(__file__).parent.parent / "fixtures"


def test_context_payload_loads_from_fixture():
    data = json.loads((FIXTURES / "sample_context_payload.json").read_text())
    payload = ContextPayload.model_validate(data)
    assert payload.payload_id == "test-psychology-001"
    assert len(payload.core_facts) == 7
    pivot_facts = [f for f in payload.core_facts if f.pivot_point]
    assert len(pivot_facts) == 3


def test_tension_map_loads_from_fixture():
    data = json.loads((FIXTURES / "fixture_tension_map.json").read_text())
    tm = TensionMap.model_validate(data)
    assert tm.overall_peak_minute == 18
    assert len(tm.acts) == 5
    assert all(1 <= act.act_number <= 5 for act in tm.acts)


def test_sensory_script_loads_from_fixture():
    data = json.loads((FIXTURES / "fixture_sensory_script.json").read_text())
    ss = SensoryScript.model_validate(data)
    assert len(ss.lines) == 5
    assert len(ss.sfx_markers) == 2


def test_subtext_review_loads_from_fixture():
    data = json.loads((FIXTURES / "fixture_subtext_review.json").read_text())
    sr = SubtextReview.model_validate(data)
    assert sr.approved is True
    assert sr.quality_score == 8.2
    assert len(sr.issues) == 1


def test_scene_loads_from_fixture():
    data = json.loads((FIXTURES / "sample_scene.json").read_text())
    scenes = [Scene.model_validate(s) for s in data]
    assert len(scenes) == 1
    assert scenes[0].scene_id == "01"


def test_core_fact_emotional_weight_validation():
    with pytest.raises(Exception):
        CoreFact(fact_id="f01", statement="test", emotional_weight=1.5)

    with pytest.raises(Exception):
        CoreFact(fact_id="f01", statement="test", emotional_weight=-0.1)


def test_vibe_parameters_bounds():
    with pytest.raises(Exception):
        VibeParameters(voice_id="test", stability=1.5, similarity_boost=0.8, style_exaggeration=0.1)
