#!/usr/bin/env python3
"""ContentAgent CLI — autonomous video creation pipeline."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.logging import RichHandler

from agent.config import Config, cfg
from agent.pipeline import Pipeline

console = Console()


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
    )


@click.group()
@click.option("--work-dir", type=click.Path(), default=None, help="Override working directory")
@click.option("--log-level", type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]), default=None)
@click.pass_context
def cli(ctx, work_dir, log_level):
    """ContentAgent — autonomous video creation pipeline."""
    config = Config()
    if work_dir:
        object.__setattr__(config, "work_dir", Path(work_dir))
    if log_level:
        object.__setattr__(config, "log_level", log_level)
    _setup_logging(config.log_level)
    ctx.ensure_object(dict)
    ctx.obj["config"] = config


@cli.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option("--model", default=None, help="Generation model: kling3, veo3, wan2, seedance2, sora2")
@click.option("--qa-rounds", default=2, help="Max QA regeneration rounds")
@click.pass_context
def recreate(ctx, video_path, model, qa_rounds):
    """Analyze a reference video and recreate it."""
    config: Config = ctx.obj["config"]
    if model:
        object.__setattr__(config, "default_gen_model", model)

    config.require("google_ai_key")

    pipeline = Pipeline(config)
    output = pipeline.recreate(video_path, max_qa_rounds=qa_rounds)
    console.print(f"\n[bold green]Output:[/] {output}")


@cli.command()
@click.argument("script", type=str)
@click.option("--style-ref", type=click.Path(exists=True), default=None,
              help="Reference video for visual style extraction")
@click.option("--model", default=None, help="Generation model")
@click.pass_context
def generate(ctx, script, style_ref, model):
    """Generate video from a text script."""
    config: Config = ctx.obj["config"]
    if model:
        object.__setattr__(config, "default_gen_model", model)

    config.require("google_ai_key")

    pipeline = Pipeline(config)
    output = pipeline.script_to_video(script, style_ref=style_ref)
    console.print(f"\n[bold green]Output:[/] {output}")


@cli.command()
@click.argument("script", type=str)
@click.argument("style_video", type=click.Path(exists=True))
@click.option("--model", default=None, help="Generation model")
@click.pass_context
def transfer(ctx, script, style_video, model):
    """Generate video from script using another video's visual style."""
    config: Config = ctx.obj["config"]
    if model:
        object.__setattr__(config, "default_gen_model", model)

    config.require("google_ai_key", "fal_key")

    pipeline = Pipeline(config)
    output = pipeline.script_to_video(script, style_ref=style_video)
    console.print(f"\n[bold green]Output:[/] {output}")


@cli.command()
@click.argument("manifest_path", type=click.Path(exists=True))
@click.pass_context
def resume(ctx, manifest_path):
    """Resume generation from a saved manifest (re-generate failed shots)."""
    from agent.models.manifest import Manifest

    config: Config = ctx.obj["config"]
    config.require("google_ai_key")

    manifest = Manifest.load(Path(manifest_path))
    pipeline = Pipeline(config)

    fails = manifest.shots_needing_regeneration()
    if not fails:
        console.print("[green]All shots already passed QA. Nothing to do.[/]")
        return

    console.print(f"Resuming: {len(fails)} shots need regeneration")
    manifest = pipeline._generate_and_qa_loop(manifest, max_rounds=2)
    output = pipeline.assembly.run(manifest)
    console.print(f"\n[bold green]Output:[/] {output}")


@cli.command()
@click.argument("manifest_path", type=click.Path(exists=True))
def inspect(manifest_path):
    """Print manifest summary."""
    from agent.models.manifest import Manifest
    from rich.table import Table

    manifest = Manifest.load(Path(manifest_path))

    console.print(f"\n[bold]Source:[/] {manifest.source_path}")
    console.print(f"[bold]Duration:[/] {manifest.source_duration}")
    console.print(f"[bold]Mode:[/] {manifest.pipeline_mode}")
    console.print(f"[bold]Style:[/] {manifest.global_style or 'N/A'}")
    console.print(f"[bold]Characters:[/] {len(manifest.identity_anchors)}")

    table = Table(title=f"Shots ({manifest.total_shots})")
    table.add_column("#", style="dim")
    table.add_column("Time")
    table.add_column("Type")
    table.add_column("Camera")
    table.add_column("Model")
    table.add_column("QA", justify="center")

    for s in manifest.shots:
        qa = "[green]PASS[/]" if s.qa_passed else ("[red]FAIL[/]" if s.qa_passed is False else "[dim]--[/]")
        table.add_row(
            str(s.shot_id),
            f"{s.timecode_start} - {s.timecode_end}",
            s.shot_type.value,
            s.camera_movement.value,
            s.generation_model or "default",
            qa,
        )
    console.print(table)


if __name__ == "__main__":
    cli()
