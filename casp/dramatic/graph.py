"""LangGraph StateGraph definition for the Dramatic Processing Engine.

Graph flow:
  START
    → tension_architect   (generates TensionMap)
    → sensory_renderer    (sensory infusion)
    → subtext_editor      (quality gate)
    → audio_tagger        (converts to Scene list)  OR  loop back to tension_architect
  END
"""

import json

from langgraph.graph import END, START, StateGraph

from casp.models.dramatic import SensoryScript
from casp.models.pipeline_state import PipelineState
from casp.models.scene import DialogueLayer, EmotionTag, Scene, VibeParameters
from casp.dramatic.agents.tension_architect import tension_architect_node
from casp.dramatic.agents.sensory_renderer import sensory_renderer_node
from casp.dramatic.agents.subtext_editor import subtext_editor_node
from casp.dramatic.state import route_after_editor
from casp.synthesis.parameter_mapper import map_emotion_to_vibe
from casp.utils.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_VOICE_ID = "Adam_Deep_Voice"


def audio_tagger_node(state: PipelineState) -> dict:
    """Convert the final SensoryScript into a list of Scene objects.

    This node does NOT call Claude — it's a pure structural transformation.
    """
    sensory_script: SensoryScript = state["sensory_script"]

    # Group lines by act_number
    acts: dict[int, list] = {}
    for line in sensory_script.lines:
        acts.setdefault(line.act_number, []).append(line)

    scenes: list[Scene] = []
    for act_num in sorted(acts.keys()):
        lines = acts[act_num]
        audio_layers = []

        for line in lines:
            emotion = EmotionTag(line.emotion_tag) if line.emotion_tag in EmotionTag._value2member_map_ else EmotionTag.PROFESSIONAL_NARRATION
            vibe_params = map_emotion_to_vibe(emotion, voice_id=_DEFAULT_VOICE_ID)

            audio_layers.append(
                DialogueLayer(
                    speaker=line.speaker,
                    text=line.sensory_text,
                    emotion_tag=emotion,
                    vibe_parameters=vibe_params,
                    post_pause="0.8s",
                )
            )

        # Insert SFX markers that belong after lines in this act
        for sfx in sensory_script.sfx_markers:
            if f"_{act_num:02d}_" in sfx.position or f"act_{act_num}" in sfx.position:
                from casp.models.scene import SFXLayer
                audio_layers.append(
                    SFXLayer(type=sfx.sound_type, volume=sfx.volume_db, duration_ms=sfx.duration_ms)
                )

        # Determine atmosphere from dominant tension emotion in this act
        tension_map = state.get("tension_map")
        atmosphere = "Dramatic"
        if tension_map and act_num <= len(tension_map.acts):
            act = tension_map.acts[act_num - 1]
            if act.tension_arc:
                peak = max(act.tension_arc, key=lambda t: t.tension_value)
                atmosphere = f"{peak.dominant_emotion.title()} / Tension {peak.tension_value:.0f}/10"

        scenes.append(
            Scene(
                scene_id=f"{act_num:02d}",
                atmosphere=atmosphere,
                act_number=act_num,
                audio_layers=audio_layers,
            )
        )

    log_entry = f"Audio Tagger: assembled {len(scenes)} scenes"
    logger.info(log_entry)

    return {
        "scenes": scenes,
        "revision_log": [log_entry],
    }


def build_dramatic_graph() -> StateGraph:
    """Build and compile the Dramatic Processing Engine state graph."""
    builder = StateGraph(PipelineState)

    builder.add_node("tension_architect", tension_architect_node)
    builder.add_node("sensory_renderer", sensory_renderer_node)
    builder.add_node("subtext_editor", subtext_editor_node)
    builder.add_node("audio_tagger", audio_tagger_node)

    builder.add_edge(START, "tension_architect")
    builder.add_edge("tension_architect", "sensory_renderer")
    builder.add_edge("sensory_renderer", "subtext_editor")

    builder.add_conditional_edges(
        "subtext_editor",
        route_after_editor,
        {"audio_tagger": "audio_tagger", "tension_architect": "tension_architect"},
    )

    builder.add_edge("audio_tagger", END)

    return builder.compile()
