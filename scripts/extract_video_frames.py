#!/usr/bin/env python3
"""Extract ordered PNG frames from a source animation video with FFmpeg."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def run(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def ffprobe_metadata(ffprobe: str, source: Path) -> dict[str, object]:
    command = [
        ffprobe,
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,r_frame_rate,avg_frame_rate,nb_frames,duration",
        "-of",
        "json",
        str(source),
    ]
    try:
        result = run(command)
        return json.loads(result.stdout or "{}")
    except (subprocess.CalledProcessError, json.JSONDecodeError) as error:
        return {"error": str(error), "command": command}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="Source video path.")
    parser.add_argument("--output-dir", required=True, help="Directory for extracted PNG frames.")
    parser.add_argument("--fps", default="", help="Optional constant output FPS.")
    parser.add_argument("--crop", default="", help="Optional FFmpeg crop expression.")
    parser.add_argument("--pattern", default="frame_%04d.png")
    parser.add_argument("--start-number", type=int, default=1)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--ffprobe", default="ffprobe")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source = Path(args.input).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"source video not found: {source}")
    if shutil.which(args.ffmpeg) is None:
        raise SystemExit(f"ffmpeg not found: {args.ffmpeg}")
    if args.ffprobe and shutil.which(args.ffprobe) is None:
        raise SystemExit(f"ffprobe not found: {args.ffprobe}")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"output directory is not empty; pass --overwrite: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        for frame in output_dir.glob("*.png"):
            frame.unlink()

    filters: list[str] = []
    mode = "source-frame-passthrough"
    if args.crop:
        filters.append(f"crop={args.crop}")
    if args.fps:
        filters.append(f"fps={args.fps}")
        mode = "constant-fps"

    command = [
        args.ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if args.overwrite else "-n",
        "-i",
        str(source),
    ]
    if filters:
        command.extend(["-vf", ",".join(filters)])
    command.extend(["-start_number", str(args.start_number), str(output_dir / args.pattern)])
    run(command)

    frames = sorted(output_dir.glob("*.png"))
    report = {
        "ok": True,
        "input": str(source),
        "output_dir": str(output_dir),
        "pattern": args.pattern,
        "requested_fps": args.fps or None,
        "crop": args.crop or None,
        "mode": mode,
        "source_metadata": ffprobe_metadata(args.ffprobe, source) if args.ffprobe else None,
        "extracted_frame_count": len(frames),
        "ffmpeg_command": command,
    }
    report_path = output_dir / "extraction_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
