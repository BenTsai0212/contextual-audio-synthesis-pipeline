from pydantic import BaseModel, Field


class TensionPoint(BaseModel):
    minute: int
    tension_value: float = Field(ge=1.0, le=10.0)
    dominant_emotion: str  # e.g. "dread", "revelation", "numbness"
    narrative_note: str


class Act(BaseModel):
    act_number: int  # 1-5
    title: str
    tension_arc: list[TensionPoint]
    script_draft: str  # Raw prose from Architect


class TensionMap(BaseModel):
    overall_peak_minute: int
    acts: list[Act]
    revision_notes: str = ""  # Populated by Subtext Editor on loop iterations


class SensoryLine(BaseModel):
    line_id: str
    speaker: str
    original_text: str
    sensory_text: str  # Rewritten with physical/sensory detail
    ambient_tags: list[str] = []   # e.g. ["electrical_buzz", "footsteps"]
    physical_actions: list[str] = []  # e.g. ["drumming fingers", "averted gaze"]
    act_number: int
    emotion_tag: str = "professional_narration"


class SFXMarker(BaseModel):
    position: str  # e.g. "after_line_03"
    sound_type: str  # e.g. "electrical_buzz"
    volume_db: str = "-12db"
    duration_ms: int | None = None


class SensoryScript(BaseModel):
    lines: list[SensoryLine]
    sfx_markers: list[SFXMarker] = []


class SubtextIssue(BaseModel):
    line_id: str
    issue_type: str  # "too_direct" | "ai_sounding" | "inconsistent_subtext"
    original_text: str
    critique: str
    suggested_rewrite: str | None = None


class SubtextReview(BaseModel):
    approved: bool
    issues: list[SubtextIssue]
    overall_notes: str
    quality_score: float = Field(ge=0.0, le=10.0)
