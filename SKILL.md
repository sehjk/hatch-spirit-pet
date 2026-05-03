---
name: hatch-spirit-pet
description: Create, repair, validate, preview, and package Codex-compatible animated spirit pets: compact 2D sprites with configurable style, identity, actions, powers, moods, rituals, movement, and special moments. Use when a user wants a Codex custom pet that can be a fighter spirit, forest spirit, ghost, elemental, mascot, familiar, robot, object spirit, or other original animated character while still loading as a normal Codex custom pet.
---

# Hatch Spirit Pet

## Overview

Create a Codex-compatible animated custom pet that looks and behaves like a small original spirit, mascot, familiar, fighter, creature, object-persona, or stylized character. This is a fork of `$hatch-fighter-pet`: it keeps the exact Codex pet atlas/package contract, but makes the nine Codex animation rows configurable for different styles and action languages.

This is a Codex-first skill. Python scripts prepare, record, validate, repair, and package runs; they do not spawn Codex subagents or call the built-in `$imagegen` runtime. Codex is the orchestrator for the normal agentic path.

The skill supports two motion sources:

- `$imagegen` row strips: default path, inherited from `$hatch-pet`.
- Video-derived rows: optional LayrKits-style intake for hard motion such as dashes, jumps, rituals, transformations, reactions, dances, loops, and special powers. The user or agent supplies a chroma-keyed video, then this skill extracts/selects/processes frames into Codex row strips.

The final output is still a normal Codex custom pet:

```text
${CODEX_HOME:-$HOME/.codex}/pets/<spirit-name>/
  pet.json
  spritesheet.webp
```

## Preset Model

This skill compiles four inputs into Codex-safe prompts:

1. Concept: the spirit identity, references, name, and short description.
2. Art style: a preset such as `pixel-art`, `stylized-3d`, `soft-clay`, `anime`, or `custom`.
3. Action style: a preset such as `fighter`, `superhero`, `cozy`, `ghostly`, `magical`, `utility`, or `custom`.
4. State overrides: optional `state=action` overrides for any fixed Codex row.

The art preset translates visual language into a tiny transparent sprite-safe prompt. The action preset maps the fixed Codex states to action intent. Overrides win over the action preset for the named state.

## Row Semantics

The Codex app still reads the same fixed rows and frame counts. Do not change row order, atlas size, cell size, or package shape. Interpret each row according to the requested action style and state overrides.

| Row | Codex state | Default generic slot | Frames |
| --- | --- | --- | ---: |
| 0 | `idle` | signature idle / breathing / hover | 6 |
| 1 | `running-right` | travel right / glide / scamper / dash | 8 |
| 2 | `running-left` | travel left / glide / scamper / dash | 8 |
| 3 | `waving` | greeting / flourish / charm / ritual | 4 |
| 4 | `jumping` | hop / float / leap / transformation beat | 5 |
| 5 | `failed` | startled / sad / dispelled / tired | 8 |
| 6 | `waiting` | anticipation / charge / listening / ambient loop | 6 |
| 7 | `running` | active work loop / hurry / patrol / pursuit | 6 |
| 8 | `review` | special moment / reveal / spell / celebration | 6 |

## Visual Style

The spirit must be original. It may be a fighter spirit, cozy spirit, forest spirit, ghost, elemental, robot, object spirit, mascot, familiar, or any other compact animated character, but it must not reproduce protected characters, logos, names, signature costumes, or exact moves.

Default style:

- compact 2D game sprite, readable inside `192x208`
- full-body or full-object character with strong silhouette and clear readable parts
- thick dark 1-2 px outline, sprite-like hard edges, limited palette, flat cel shading
- original face/expression language, body/object design, costume/prop/accessory, and motif
- no scenery, floor, shadows, UI, text, watermarks, speech bubbles, or copied layout guides

## Effects And Attachments

Effects are allowed when they remain usable in a tiny Codex cell and serve the requested spirit style.

Allowed:

- flame fists touching the hands
- lightning wrapped around a weapon or gauntlet
- aura tightly hugging or overlapping the body/object
- sparkles, leaves, bubbles, static, runes, embers, or smoke attached to the silhouette
- small hard-edged impact, magic, emotion, or activity marks touching the body/object/prop

Rejected:

- detached particles, floating icons, text, UI marks, loose symbols
- broad transparent glow haze, bloom, soft aura clouds, motion blur, smears
- cast shadows, floor shadows, scenery, backgrounds, camera shake, zoom, cuts
- effects crossing into a neighboring frame slot
- chroma-key-adjacent colors in the spirit or effects

Rows such as `waiting` and `review` may be more dramatic, but the spirit identity must stay consistent.

## Generation Delegation

Use `$imagegen` for normal visual generation. Before generating base art or imagegen row strips, load:

```text
${CODEX_HOME:-$HOME/.codex}/skills/.system/imagegen/SKILL.md
```

Do not call image APIs directly for the normal path. The base job may be prompt-only. Every `$imagegen` row-strip job must use the listed grounding images from `imagegen-jobs.json`, including the canonical base reference and the row layout guide.

For video-derived rows, do not use `$imagegen` to draw missing frames. Use supplied video frames only, through this skill's deterministic scripts.

Parent-agent responsibilities:

- read or prepare `imagegen-jobs.json`
- generate and record the base job
- decide whether `running-left` can be mirrored
- record selected built-in `$imagegen` outputs with `record_imagegen_result.py`
- run `queue_pet_repairs.py`, `finalize_pet_run.py`, atlas validation, previews, and packaging

Subagent responsibilities:

- generate assigned row strips only
- use row prompts and grounding images supplied by the manifest
- return the selected original `$CODEX_HOME/generated_images/.../ig_*.png` path and a short QA note
- never edit manifests, write `decoded/`, mirror rows, finalize, repair, or package

## Default Workflow

1. Prepare a run:

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/hatch-spirit-pet"
python "$SKILL_DIR/scripts/prepare_pet_run.py" \
  --pet-name "<Name>" \
  --description "<one sentence>" \
  --pet-notes "<original spirit concept>" \
  --art-style "<pixel-art|stylized-3d|soft-clay|anime|custom>" \
  --action-style "<fighter|superhero|cozy|ghostly|magical|utility|custom>" \
  --state-action 'review=<optional specific review action>' \
  --style-notes "<optional style notes>" \
  --action-notes "<optional row/action notes>" \
  --output-dir /absolute/path/to/run \
  --force
```

Optional command-builder UI:

```text
${CODEX_HOME:-$HOME/.codex}/skills/hatch-spirit-pet/ui/index.html
```

Open that file in a browser to toggle presets, edit row actions, and copy a complete `prepare_pet_run.py` command. The UI prepares the run command only; complete generation, subagent delegation, repairs, QA, and packaging in Codex.

After preparing a run, the user can ask:

```text
Use hatch-spirit-pet to finish this run with sub-agents: /absolute/path/to/run
```

2. Generate and record the base with `$imagegen`, then inspect ready jobs:

```bash
python "$SKILL_DIR/scripts/pet_job_status.py" --run-dir /absolute/path/to/run
```

3. Complete rows by either path:

- `$imagegen` path: generate the row strip from its prompt and input images, then record with `record_imagegen_result.py`.
- Video path: process an external chroma-keyed clip into a completed decoded row:

```bash
python "$SKILL_DIR/scripts/extract_video_frames.py" \
  --input /absolute/path/to/source-video.mp4 \
  --output-dir /absolute/path/to/run/video/extracted/review \
  --overwrite

python "$SKILL_DIR/scripts/select_video_frames.py" \
  --source-dir /absolute/path/to/run/video/extracted/review \
  --output-dir /absolute/path/to/run/video/selected/review \
  --indices "1,8,15,22,29,36" \
  --frame-prefix review \
  --beat-labels "ready,charge,release,impact,follow-through,recover"

python "$SKILL_DIR/scripts/process_power_frames.py" \
  --run-dir /absolute/path/to/run \
  --state review \
  --source-frames-dir /absolute/path/to/run/video/selected/review \
  --source-video /absolute/path/to/source-video.mp4 \
  --background-mode chroma \
  --chroma-key '#00FF00' \
  --selection-note "video-derived special power beats"
```

`process_power_frames.py` writes `decoded/<state>.png`, frame cells, preview/report files, and marks that job complete with `source_provenance: video-derived-row`.

4. For `running-left`, mirror `running-right` only when the design is safe to mirror. Otherwise generate or process a left-facing row normally.

5. Finalize:

```bash
python "$SKILL_DIR/scripts/finalize_pet_run.py" --run-dir /absolute/path/to/run
```

Review `qa/contact-sheet.png`, `qa/review.json`, `final/validation.json`, and `qa/videos/` before accepting the spirit.

## Subagent Row Generation

After the base job has been recorded, row-strip visual generation via `$imagegen` should use subagents unless the user explicitly says not to. The parent owns manifests, recording, video processing, finalization, repairs, and packaging.

Subagents may only generate image rows and return the selected original `$CODEX_HOME/generated_images/.../ig_*.png` source path plus a short QA note. They must not edit manifests, copy into `decoded/`, run video scripts, record results, mirror rows, finalize, repair, or package.

Video-derived rows stay with the parent because they mutate the manifest and decoded outputs deterministically from supplied clips.

If a user runs only `python scripts/prepare_pet_run.py`, no subagents will run. Subagents require Codex runtime and must be triggered by asking Codex to finish the prepared run.

## Repair Workflow

If finalization fails, use the smallest repair scope:

```bash
python "$SKILL_DIR/scripts/queue_pet_repairs.py" --run-dir /absolute/path/to/run
```

Regenerate only failed `$imagegen` rows, or rerun only the failed video-derived row with a better source clip or frame selection.

## Acceptance Criteria

- Final atlas is PNG/WebP `1536x1872`, transparent-capable, with `192x208` cells.
- Used cells are non-empty and unused cells are transparent.
- Row/frame counts match `references/animation-rows.md`.
- `qa/review.json` has no errors.
- Preview videos and contact sheet exist unless explicitly skipped.
- The spirit identity, palette, face/expression language, body/object design, costume/prop/accessory, and motif stay consistent across rows.
- Effects are attached, hard-edged, readable, and contained inside each frame slot.
- No copied guide marks, text, UI, scenery, detached VFX, broad glow haze, clipping, slot overlap, or background artifacts.
