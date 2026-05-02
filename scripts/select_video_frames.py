#!/usr/bin/env python3
"""Select explicit animation beats from extracted video frames."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

IMAGE_SUFFIXES = {".png", ".webp", ".jpg", ".jpeg"}


def natural_key(path: Path) -> list[object]:
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", path.name)]


def parse_indices(raw: str) -> list[int]:
    indices: list[int] = []
    for chunk in raw.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            start_raw, end_raw = chunk.split("-", 1)
            start = int(start_raw.strip())
            end = int(end_raw.strip())
            if end < start:
                raise SystemExit(f"invalid descending range: {chunk}")
            indices.extend(range(start, end + 1))
        else:
            indices.append(int(chunk))
    if not indices:
        raise SystemExit("no frame indices provided")
    if any(index < 1 for index in indices):
        raise SystemExit("frame indices are 1-based and must be >= 1")
    return indices


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--indices", required=True, help="1-based indices, e.g. 1,6,12 or 1-6.")
    parser.add_argument("--frame-prefix", required=True)
    parser.add_argument("--beat-labels", default="", help="Optional comma-separated labels matching selected frames.")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    source_dir = Path(args.source_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"source frame directory not found: {source_dir}")
    source_frames = sorted(
        [path for path in source_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES],
        key=natural_key,
    )
    if not source_frames:
        raise SystemExit(f"no image frames found in {source_dir}")
    indices = parse_indices(args.indices)
    if max(indices) > len(source_frames):
        raise SystemExit(f"selected frame {max(indices)} but only {len(source_frames)} frames exist")

    labels = [label.strip() for label in args.beat_labels.split(",") if label.strip()]
    if labels and len(labels) != len(indices):
        raise SystemExit("--beat-labels must match the selected frame count")
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise SystemExit(f"output directory is not empty; pass --overwrite: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.overwrite:
        for path in output_dir.iterdir():
            if path.is_file():
                path.unlink()

    mapping = []
    for output_index, source_index in enumerate(indices, start=1):
        source = source_frames[source_index - 1]
        target = output_dir / f"{args.frame_prefix}_{output_index:04d}.png"
        shutil.copy2(source, target)
        mapping.append(
            {
                "output_index": output_index,
                "output_path": str(target),
                "source_index": source_index,
                "source_path": str(source),
                "beat_label": labels[output_index - 1] if labels else "selected",
            }
        )

    report = {
        "ok": True,
        "source_dir": str(source_dir),
        "output_dir": str(output_dir),
        "total_source_frame_count": len(source_frames),
        "selected_frame_count": len(indices),
        "selected_source_indices": indices,
        "mapping": mapping,
    }
    report_path = output_dir / "selection_report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
