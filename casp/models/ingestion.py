from enum import Enum
from pydantic import BaseModel, Field


class InputType(str, Enum):
    TEXT_FILE = "text_file"
    URL = "url"
    RSS = "rss"
    JSON = "json"
    RAW_TEXT = "raw_text"


class RawInput(BaseModel):
    input_type: InputType
    content: str
    source_uri: str | None = None


class CoreFact(BaseModel):
    fact_id: str
    statement: str
    emotional_weight: float = Field(ge=0.0, le=1.0, description="0=neutral, 1=highly charged")
    pivot_point: bool = False  # True = narrative turning point


class ContextPayload(BaseModel):
    payload_id: str
    title: str
    domain: str  # e.g. "psychology", "history", "narrative"
    core_facts: list[CoreFact]
    raw_summary: str
    word_count_original: int = 0
    metadata: dict = {}
