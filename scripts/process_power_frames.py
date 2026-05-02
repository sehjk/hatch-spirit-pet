#!/usr/bin/env python3
"""Convert selected video frames into a completed Codex spirit-pet row strip."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from PIL import Image

CELL_WIDTH = 192
CELL_HEIGHT = 208
ROW_FRAME_COUNTS = {
    "idle": 6,
    "running-right": 8,
    "running-left": 8,
    "waving": 4,
    "jumping": 5,
    "failed": 8,
    "waiting": 6,
    "running": 6,
    "review": 6,
}
IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.resolve().relative_to(root.resolve()))
    except ValueError:
        return str(path.resolve())


def parse_hex_color(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise SystemExit(f"invalid chroma key: {value}")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def remove_chroma(image: Image.Image, key: tuple[int, int, int], tolerance: int) -> Image.Image:
    rgba = image.convert("RGBA")
    pixels = rgba.load()
    width, height = rgba.size
    key_r, key_g, key_b = key
    for y in range(height):
        for x in range(width):
            red, green, blue, alpha = pixels[x, y]
            if alpha == 0:
                continue
            distance = abs(red - key_r) + abs(green - key_g) + abs(blue - key_b)
            strong_green_key = (
                key == (0, 255, 0)
                and green > 210
                and red < 80
                and blue < 80
                and green > red + 90
                and green > blue + 90
            )
            if distance <= tolerance or strong_green_key:
                pixels[x, y] = (red, green, blue, 0)
            elif key == (0, 255, 0) and green > max(red, blue) + 35:
                pixels[x, y] = (red, max(red, blue), blue, alpha)
    return rgba


def preserve_canvas_cell(source: Image.Image, *, background_mode: str, key: tuple[int, int, int], tolerance: int) -> Image.Image:
    rgba = source.convert("RGBA")
    if background_mode == "chroma":
        rgba = remove_chroma(rgba, key, tolerance)
    elif background_mode != "alpha":
        raise SystemExit(f"unknown background mode: {background_mode}")

    cell = Image.new("RGBA", (CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    scale = min(CELL_WIDTH / rgba.width, CELL_HEIGHT / rgba.height)
    scaled_size = (max(1, round(rgba.width * scale)), max(1, round(rgba.height * scale)))
    scaled = rgba.resize(scaled_size, Image.Resampling.LANCZOS)
    paste = ((CELL_WIDTH - scaled.width) // 2, (CELL_HEIGHT - scaled.height) // 2)
    cell.alpha_composite(scaled, paste)
    return cell


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def update_manifest(
    run_dir: Path,
    *,
    state: str,
    source_video: Path,
    output: Path,
    report: Path,
    selection_note: str,
) -> None:
    manifest_path = run_dir / "imagegen-jobs.json"
    manifest = load_json(manifest_path)
    jobs = manifest.get("jobs")
    if not isinstance(jobs, list):
        raise SystemExit("invalid imagegen-jobs.json: jobs must be a list")
    for job in jobs:
        if isinstance(job, dict) and job.get("id") == state:
            job.update(
                {
                    "status": "complete",
                    "motion_source": "video",
                    "source_provenance": "video-derived-row",
                    "source_path": str(source_video),
                    "output_path": rel(output, run_dir),
                    "output_sha256": file_sha256(output),
                    "video_processing_report": rel(report, run_dir),
                    "selection_note": selection_note,
                    "recording_owner": "parent",
                }
            )
            write_json(manifest_path, manifest)
            return
    raise SystemExit(f"job not found in imagegen-jobs.json: {state}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--state", required=True, choices=sorted(ROW_FRAME_COUNTS))
    parser.add_argument("--source-frames-dir", required=True)
    parser.add_argument("--source-video", required=True)
    parser.add_argument("--background-mode", choices=["chroma", "alpha"], default="chroma")
    parser.add_argument("--chroma-key", default="#00FF00")
    parser.add_argument("--tolerance", type=int, default=24)
    parser.add_argument("--selection-note", default="video-derived row")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    run_dir = Path(args.run_dir).expanduser().resolve()
    source_frames_dir = Path(args.source_frames_dir).expanduser().resolve()
    source_video = Path(args.source_video).expanduser().resolve()
    if not (run_dir / "imagegen-jobs.json").is_file():
        raise SystemExit(f"run dir is missing imagegen-jobs.json: {run_dir}")
    if not source_frames_dir.is_dir():
        raise SystemExit(f"source frames directory not found: {source_frames_dir}")
    if not source_video.is_file():
        raise SystemExit(f"source video not found: {source_video}")

    frames = sorted(
        [path for path in source_frames_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES],
        key=natural_key,
    )
    expected = ROW_FRAME_COUNTS[args.state]
    if len(frames) != expected:
        raise SystemExit(f"{args.state} needs exactly {expected} selected frames, found {len(frames)}")

    output = run_dir / "decoded" / f"{args.state}.png"
    cells_dir = run_dir / "video" / "processed" / args.state / "cells"
    preview = run_dir / "video" / "processed" / args.state / "preview.png"
    report_path = run_dir / "video" / "processed" / args.state / "processing_report.json"
    if output.exists() and not args.overwrite:
        raise SystemExit(f"decoded row already exists; pass --overwrite: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    cells_dir.mkdir(parents=True, exist_ok=True)
    preview.parent.mkdir(parents=True, exist_ok=True)

    key = parse_hex_color(args.chroma_key)
    strip = Image.new("RGBA", (expected * CELL_WIDTH, CELL_HEIGHT), (0, 0, 0, 0))
    cell_reports = []
    for index, frame_path in enumerate(frames):
        with Image.open(frame_path) as source:
            cell = preserve_canvas_cell(
                source,
                background_mode=args.background_mode,
                key=key,
                tolerance=args.tolerance,
            )
        bbox = alpha_bbox(cell)
        if bbox is None:
            raise SystemExit(f"processed frame became fully transparent: {frame_path}")
        cell_path = cells_dir / f"{args.state}_{index + 1:04d}.png"
        cell.save(cell_path)
        strip.alpha_composite(cell, (index * CELL_WIDTH, 0))
        cell_reports.append(
            {
                "index": index + 1,
                "source": str(frame_path),
                "cell": str(cell_path),
                "alpha_bbox": list(bbox),
            }
        )

    strip.save(output)
    checker = Image.new("RGBA", strip.size, (255, 255, 255, 255))
    checker.alpha_composite(strip)
    checker.save(preview)

    report = {
        "ok": True,
        "state": args.state,
        "source_video": str(source_video),
        "source_frames_dir": str(source_frames_dir),
        "frame_count": expected,
        "cell_size": [CELL_WIDTH, CELL_HEIGHT],
        "output": str(output),
        "output_sha256": file_sha256(output),
        "background_mode": args.background_mode,
        "chroma_key": args.chroma_key,
        "tolerance": args.tolerance,
        "layout_mode": "preserve-canvas",
        "selection_note": args.selection_note,
        "cells": cell_reports,
    }
    write_json(report_path, report)
    update_manifest(
        run_dir,
        state=args.state,
        source_video=source_video,
        output=output,
        report=report_path,
        selection_note=args.selection_note,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
