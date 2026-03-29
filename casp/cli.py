"""CASP CLI — Contextual Audio Synthesis Pipeline command-line interface."""

import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from casp.utils.logging import setup_logging

app = typer.Typer(
    name="casp",
    help="Contextual Audio Synthesis Pipeline — Multi-Agent Podcast Production",
    add_completion=False,
)
console = Console()


@app.command()
def run(
    input_path: str = typer.Argument(..., help="Path to input file (text, JSON, URL, RSS)"),
    input_type: Optional[str] = typer.Option(
        None, "--type", "-t",
        help="Input type: text|json|url|rss (auto-detected if omitted)",
    ),
    output_dir: Path = typer.Option(
        Path("./output"), "--output", "-o", help="Output directory"
    ),
    no_audio: bool = typer.Option(
        False, "--no-audio", help="Skip ElevenLabs synthesis; produce script JSON only (MVP mode)"
    ),
    max_iter: int = typer.Option(
        3, "--max-iter", "-n", help="Maximum dramatic processing iterations"
    ),
    voice_profile: Optional[str] = typer.Option(
        None, "--voice-profile", help="ElevenLabs voice ID override"
    ),
    verbose: bool = typer.Option(False, "--verbose", "-v"),
) -> None:
    """Run the full CASP pipeline on an input source."""
    setup_logging(verbose=verbose)

    from casp.ingestion.loader import InputType as IT, load_context_payload
    from casp.ingestion.denoiser import denoise
    from casp.models.ingestion import RawInput
    from casp.dramatic.graph import build_dramatic_graph

    # Map CLI type string to enum
    type_map = {
        "text": IT.TEXT_FILE,
        "json": IT.JSON,
        "url": IT.URL,
        "rss": IT.RSS,
    }
    it = type_map.get(input_type) if input_type else None

    console.print(f"[bold cyan]CASP[/] Loading input: [yellow]{input_path}[/]")

    # Stage 1: Load and denoise
    result = load_context_payload(input_path, it)

    if isinstance(result, RawInput):
        console.print("[cyan]Denoising raw input...[/]")
        payload = denoise(result)
    else:
        payload = result
        console.print(f"[green]Loaded ContextPayload:[/] '{payload.title}' ({len(payload.core_facts)} facts)")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Stage 2: Dramatic Processing Engine
    console.print("[cyan]Starting Dramatic Processing Engine...[/]")

    graph = build_dramatic_graph()
    final_state = graph.invoke({
        "context_payload": payload,
        "tension_map": None,
        "sensory_script": None,
        "subtext_review": None,
        "iteration": 0,
        "max_iterations": max_iter,
        "quality_approved": False,
        "scenes": None,
        "revision_log": [],
    })

    scenes = final_state["scenes"]
    console.print(f"[green]Script complete:[/] {len(scenes)} scenes generated")

    # Save script JSON
    scenes_path = output_dir / "scenes.json"
    scenes_data = [s.model_dump() for s in scenes]
    scenes_path.write_text(
        json.dumps(scenes_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    console.print(f"[green]Script saved:[/] {scenes_path}")

    # Save revision log
    log_path = output_dir / "revision_log.txt"
    log_path.write_text("\n".join(final_state.get("revision_log", [])), encoding="utf-8")

    if no_audio:
        console.print("[yellow]--no-audio flag set. Skipping ElevenLabs synthesis.[/]")
        console.print("[bold green]Done![/] Output in:", output_dir)
        return

    # Stage 3: Audio Synthesis
    console.print("[cyan]Generating audio segments...[/]")
    from casp.synthesis.elevenlabs_client import generate_segment
    from casp.synthesis.audio_assembler import assemble

    segment_dir = output_dir / "segments"
    segment_dir.mkdir(exist_ok=True)

    for scene in scenes:
        for idx, layer in enumerate(scene.audio_layers):
            from casp.models.scene import DialogueLayer
            if isinstance(layer, DialogueLayer):
                seg_path = segment_dir / f"scene_{scene.scene_id}_layer_{idx:03d}.mp3"
                if voice_profile:
                    layer.vibe_parameters.voice_id = voice_profile
                generate_segment(layer, seg_path)

    # Assemble final audio
    episode_path = output_dir / "episode.mp3"
    assemble(scenes, segment_dir, episode_path)
    console.print(f"[bold green]Episode ready:[/] {episode_path}")


@app.command()
def validate(
    scene_json: Path = typer.Argument(..., help="Path to scenes.json to validate"),
) -> None:
    """Validate a scenes.json file against the CASP schema."""
    from casp.models.scene import Scene

    data = json.loads(scene_json.read_text(encoding="utf-8"))
    errors = []
    for i, item in enumerate(data):
        try:
            Scene.model_validate(item)
        except Exception as e:
            errors.append(f"Scene {i}: {e}")

    if errors:
        console.print("[red]Validation failed:[/]")
        for err in errors:
            console.print(f"  [red]FAIL[/] {err}")
        raise typer.Exit(1)

    console.print(f"[green]OK All {len(data)} scenes are valid.[/]")


@app.command()
def voices() -> None:
    """List available ElevenLabs voices."""
    from casp.synthesis.elevenlabs_client import list_voices

    voice_list = list_voices()
    table = Table("Voice ID", "Name")
    for v in voice_list:
        table.add_row(v["voice_id"], v["name"])
    console.print(table)


@app.command("emotion-map")
def emotion_map() -> None:
    """Show the EmotionTag → ElevenLabs parameter mapping table."""
    from casp.synthesis.parameter_mapper import get_all_mappings

    mappings = get_all_mappings()
    table = Table("EmotionTag", "stability", "similarity_boost", "style_exaggeration", "speed")
    for tag, params in mappings.items():
        table.add_row(
            tag,
            str(params["stability"]),
            str(params["similarity_boost"]),
            str(params["style_exaggeration"]),
            str(params["speed"]),
        )
    console.print(table)


if __name__ == "__main__":
    app()
