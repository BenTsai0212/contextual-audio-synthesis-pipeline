"""Audio Assembler — stitches per-segment MP3s into a final podcast episode.

Uses pydub for concatenation. Requires ffmpeg installed on the system.
"""

import re
from pathlib import Path

from casp.models.scene import DialogueLayer, Scene, SFXLayer
from casp.utils.logging import get_logger

logger = get_logger(__name__)


def _pause_ms(pause_str: str) -> int:
    """Convert a pause string like '1.2s' or '800ms' to milliseconds."""
    pause_str = pause_str.strip()
    if pause_str.endswith("ms"):
        return int(float(pause_str[:-2]))
    if pause_str.endswith("s"):
        return int(float(pause_str[:-1]) * 1000)
    return 500  # default 500ms


def assemble(
    scenes: list[Scene],
    segment_dir: Path,
    output_path: Path,
) -> Path:
    """Concatenate all scene audio segments into a single MP3 file.

    Parameters
    ----------
    scenes:
        The final list of Scene objects from the pipeline.
    segment_dir:
        Directory containing per-layer MP3 files named
        ``scene_{scene_id}_layer_{idx:03d}.mp3``.
    output_path:
        Destination path for the final assembled MP3.

    Returns
    -------
    Path to the assembled audio file.
    """
    try:
        from pydub import AudioSegment
        from pydub.generators import Sine
    except ImportError:
        raise RuntimeError("pydub not installed. Run: pip install pydub")

    assembled = AudioSegment.silent(duration=0)

    for scene in scenes:
        logger.info("Assembling scene %s (%d layers)", scene.scene_id, len(scene.audio_layers))

        for idx, layer in enumerate(scene.audio_layers):
            if isinstance(layer, DialogueLayer):
                seg_path = segment_dir / f"scene_{scene.scene_id}_layer_{idx:03d}.mp3"
                if not seg_path.exists():
                    logger.warning("Segment file not found, skipping: %s", seg_path)
                    continue
                seg = AudioSegment.from_mp3(str(seg_path))
                assembled += seg

                # Add post-pause
                pause_duration = _pause_ms(layer.post_pause)
                assembled += AudioSegment.silent(duration=pause_duration)

            elif isinstance(layer, SFXLayer):
                # Generate a brief tone as placeholder SFX if no file exists
                sfx_path = segment_dir / f"sfx_{layer.type.lower()}.mp3"
                if sfx_path.exists():
                    sfx = AudioSegment.from_mp3(str(sfx_path))
                    # Apply volume adjustment
                    db_match = re.search(r"(-?\d+(?:\.\d+)?)\s*db", layer.volume, re.I)
                    if db_match:
                        sfx = sfx + float(db_match.group(1))
                    assembled += sfx
                else:
                    duration = layer.duration_ms or 1000
                    assembled += AudioSegment.silent(duration=duration)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    assembled.export(str(output_path), format="mp3", bitrate="192k")
    logger.info("Assembled episode saved: %s (%.1fs)", output_path, len(assembled) / 1000)
    return output_path
