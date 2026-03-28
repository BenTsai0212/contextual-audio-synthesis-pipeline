"""ElevenLabs API wrapper for per-segment audio generation."""

from pathlib import Path

from casp.config import settings
from casp.models.scene import DialogueLayer
from casp.utils.logging import get_logger

logger = get_logger(__name__)


def generate_segment(layer: DialogueLayer, output_path: Path) -> Path:
    """Generate audio for a single DialogueLayer and save to output_path.

    Returns the path to the generated audio file.
    """
    try:
        from elevenlabs import ElevenLabs, VoiceSettings
    except ImportError:
        raise RuntimeError("elevenlabs package not installed. Run: pip install elevenlabs")

    if not settings.elevenlabs_api_key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. "
            "Add it to your .env file or use --no-audio to skip synthesis."
        )

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    vp = layer.vibe_parameters

    logger.debug(
        "ElevenLabs: voice=%s stability=%.2f speaker=%s text_len=%d",
        vp.voice_id, vp.stability, layer.speaker, len(layer.text),
    )

    audio_generator = client.text_to_speech.convert(
        voice_id=vp.voice_id,
        text=layer.text,
        model_id="eleven_multilingual_v2",
        voice_settings=VoiceSettings(
            stability=vp.stability,
            similarity_boost=vp.similarity_boost,
            style=vp.style_exaggeration,
            use_speaker_boost=True,
        ),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        for chunk in audio_generator:
            f.write(chunk)

    logger.debug("Saved segment: %s", output_path)
    return output_path


def list_voices() -> list[dict]:
    """Return available voices from ElevenLabs."""
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        raise RuntimeError("elevenlabs package not installed.")

    client = ElevenLabs(api_key=settings.elevenlabs_api_key)
    voices = client.voices.get_all()
    return [{"voice_id": v.voice_id, "name": v.name} for v in voices.voices]
