from enum import Enum
from pydantic import BaseModel, Field


class EmotionTag(str, Enum):
    TENSION_SUSPENSE = "tension_suspense"
    PROFESSIONAL_NARRATION = "professional_narration"
    INTIMATE_CONFESSION = "intimate_confession"
    CONFRONTATION = "confrontation"
    REVELATION = "revelation"


class VibeParameters(BaseModel):
    voice_id: str
    stability: float = Field(ge=0.0, le=1.0)
    similarity_boost: float = Field(ge=0.0, le=1.0)
    style_exaggeration: float = Field(ge=0.0, le=1.0)
    speed: float = Field(default=1.0, ge=0.5, le=2.0)


class SFXLayer(BaseModel):
    speaker: str = "SFX_Trigger"
    type: str  # e.g. "Electrical_Buzz"
    volume: str  # e.g. "-12db"
    duration_ms: int | None = None


class DialogueLayer(BaseModel):
    speaker: str
    text: str
    emotion_tag: EmotionTag
    vibe_parameters: VibeParameters
    post_pause: str = "0.5s"  # e.g. "1.2s"


class Scene(BaseModel):
    scene_id: str
    atmosphere: str  # e.g. "Claustrophobic / High Tension"
    act_number: int
    audio_layers: list[DialogueLayer | SFXLayer]
