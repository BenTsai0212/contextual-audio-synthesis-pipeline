"""EmotionTag → ElevenLabs VibeParameters mapping.

All mapping values are defined here as constants, never hardcoded in agent prompts.
"""

from casp.models.scene import EmotionTag, VibeParameters

# Mapping table: EmotionTag → (stability, similarity_boost, style_exaggeration, speed)
_EMOTION_PARAMS: dict[EmotionTag, tuple[float, float, float, float]] = {
    EmotionTag.TENSION_SUSPENSE:       (0.25, 0.75, 0.45, 0.90),
    EmotionTag.PROFESSIONAL_NARRATION: (0.80, 0.85, 0.05, 1.00),
    EmotionTag.INTIMATE_CONFESSION:    (0.50, 0.90, 0.20, 0.95),
    EmotionTag.CONFRONTATION:          (0.20, 0.70, 0.60, 1.05),
    EmotionTag.REVELATION:             (0.35, 0.80, 0.40, 0.92),
}


def map_emotion_to_vibe(emotion: EmotionTag, voice_id: str = "Adam_Deep_Voice") -> VibeParameters:
    """Return VibeParameters for the given EmotionTag."""
    stability, similarity_boost, style_exaggeration, speed = _EMOTION_PARAMS.get(
        emotion,
        _EMOTION_PARAMS[EmotionTag.PROFESSIONAL_NARRATION],  # safe default
    )
    return VibeParameters(
        voice_id=voice_id,
        stability=stability,
        similarity_boost=similarity_boost,
        style_exaggeration=style_exaggeration,
        speed=speed,
    )


def get_all_mappings() -> dict[str, dict]:
    """Return the full mapping table as a serializable dict (for CLI display)."""
    return {
        tag.value: {
            "stability": params[0],
            "similarity_boost": params[1],
            "style_exaggeration": params[2],
            "speed": params[3],
        }
        for tag, params in _EMOTION_PARAMS.items()
    }
