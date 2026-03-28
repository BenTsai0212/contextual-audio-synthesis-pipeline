"""Unit tests for the EmotionTag → VibeParameters mapper."""

from casp.models.scene import EmotionTag
from casp.synthesis.parameter_mapper import map_emotion_to_vibe, get_all_mappings


def test_tension_suspense_has_low_stability():
    vibe = map_emotion_to_vibe(EmotionTag.TENSION_SUSPENSE)
    assert vibe.stability < 0.5


def test_professional_narration_has_high_stability():
    vibe = map_emotion_to_vibe(EmotionTag.PROFESSIONAL_NARRATION)
    assert vibe.stability >= 0.7


def test_confrontation_has_highest_style_exaggeration():
    confrontation = map_emotion_to_vibe(EmotionTag.CONFRONTATION)
    narration = map_emotion_to_vibe(EmotionTag.PROFESSIONAL_NARRATION)
    assert confrontation.style_exaggeration > narration.style_exaggeration


def test_voice_id_is_passed_through():
    vibe = map_emotion_to_vibe(EmotionTag.REVELATION, voice_id="custom_voice_123")
    assert vibe.voice_id == "custom_voice_123"


def test_all_emotion_tags_are_mapped():
    mappings = get_all_mappings()
    for tag in EmotionTag:
        assert tag.value in mappings


def test_all_params_within_valid_range():
    for tag in EmotionTag:
        vibe = map_emotion_to_vibe(tag)
        assert 0.0 <= vibe.stability <= 1.0
        assert 0.0 <= vibe.similarity_boost <= 1.0
        assert 0.0 <= vibe.style_exaggeration <= 1.0
        assert 0.5 <= vibe.speed <= 2.0
