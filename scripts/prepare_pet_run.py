#!/usr/bin/env python3
"""Create a Codex spirit-pet run folder, prompts, and imagegen job manifest."""

from __future__ import annotations

import argparse
import json
import math
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
from PIL import ImageDraw

ATLAS = {"columns": 8, "rows": 9, "cell_width": 192, "cell_height": 208}
ATLAS["width"] = ATLAS["columns"] * ATLAS["cell_width"]
ATLAS["height"] = ATLAS["rows"] * ATLAS["cell_height"]

ROWS = [
    ("idle", 0, 6, "signature idle loop with breathing, hover, pulse, blink, or weight shift"),
    ("running-right", 1, 8, "rightward travel loop: glide, scamper, dash, float, roll, or stride"),
    ("running-left", 2, 8, "leftward travel loop: glide, scamper, dash, float, roll, or stride"),
    ("waving", 3, 4, "greeting, charm, flourish, ritual gesture, taunt, or stance change"),
    ("jumping", 4, 5, "hop, float, leap, pop-up, aerial pose, or transformation beat"),
    ("failed", 5, 8, "startled, sad, tired, dispelled, knocked-back, or defeated reaction"),
    ("waiting", 6, 6, "anticipation, charge, listening, thinking, ambient power, or quiet readiness loop"),
    ("running", 7, 6, "active work loop, hurry, patrol, pursuit, forward rush, or in-place motion loop"),
    ("review", 8, 6, "special moment, reveal, spell, flourish, celebration, finisher, or power loop"),
]

TRANSPARENCY_ARTIFACT_RULES = [
    "Effects are allowed only when state-relevant, opaque, hard-edged, sprite-like, fully inside the same frame slot, and physically touching or overlapping the spirit silhouette, body, object, prop, accessory, or motif focus.",
    "Allowed attached effects include flame, lightning, leaves, bubbles, static, runes, embers, sparkles, tight aura, impact marks, emotion marks, smoke, or crackle when they touch or overlap the spirit silhouette.",
    "Do not draw detached effects: floating stars, loose sparkles, floating punctuation, floating icons, separated smoke clouds, loose dust, disconnected outline bits, or stray pixels.",
    "Do not draw speed lines, action streaks, afterimages, blur, smears, broad glow haze, bloom, soft transparent auras, floor patches, cast shadows, contact shadows, drop shadows, oval floor shadows, landing marks, or detached impact bursts.",
    "Do not include text, labels, frame numbers, visible grids, guide marks, speech bubbles, thought bubbles, UI panels, code snippets, scenery, checkerboard transparency, white backgrounds, or black backgrounds.",
    "Do not use the chroma-key color or chroma-key-adjacent colors in the spirit, body, object, prop, accessory, effects, highlights, shadows, or outlines.",
    "Reject any pose that is cropped, overlaps another pose, crosses into a neighboring frame slot, or creates a separate disconnected component that is not attached to the spirit.",
]

STATE_REQUIREMENTS = {
    "waving": [
        "Show a greeting, charm, flourish, ritual gesture, taunt, or stance change appropriate to the selected action style.",
        "Do not draw wave marks, motion arcs, loose sparkles, symbols, or floating effects unless they physically touch or overlap the spirit.",
    ],
    "jumping": [
        "Show the leap through pose and vertical body position: anticipation, lift, airborne peak, descent, settle.",
        "For floating or ghostlike spirits, make the row read as a hop, buoyant rise, pop-up, or transformation beat rather than literal legs jumping.",
        "A small attached effect is allowed only if it touches the spirit, body, object, prop, or accessory and stays inside the slot.",
        "Do not draw ground shadows, contact shadows, drop shadows, oval shadows, landing marks, dust, smears, bounce pads, or detached motion marks under the spirit.",
        "Keep the background outside the spirit perfectly flat chroma key with no darker key-colored patches.",
    ],
    "failed": [
        "Show a startled, sad, dispelled, tired, knocked-back, or defeated reaction through pose, squash, slump, blink, wilt, dimming, or recoil.",
        "Small attached smoke, sparks, tears, static, stun stars, or emotion marks are allowed only if overlapping the spirit silhouette and kept inside the same frame slot.",
        "Do not draw red X marks, floating symbols, detached stars, separated smoke clouds, dust, or other loose effects.",
    ],
    "review": [
        "Show a special moment: reveal, spell, flourish, celebration, transformation, finisher, or power beat.",
        "Effects may touch or overlap the spirit, body, object, prop, accessory, or motif focus, but must stay hard-edged and contained inside each frame slot.",
        "Do not add UI, text, punctuation, symbols, scenery, or new unrelated props.",
    ],
    "waiting": [
        "Show anticipation, charge, listening, thinking, ambient power, quiet readiness, or attention through pose and subtle repeated motion.",
        "The effect must remain attached to or overlapping the spirit silhouette.",
    ],
    "running-right": [
        "Show rightward travel through body lean, bob, glide, scamper, roll, float, stride, or dash appropriate to the selected action style.",
        "Do not draw speed lines, dust clouds, floor shadows, motion trails, or detached motion effects.",
    ],
    "running-left": [
        "Show leftward travel through body lean, bob, glide, scamper, roll, float, stride, or dash appropriate to the selected action style.",
        "Do not draw speed lines, dust clouds, floor shadows, motion trails, or detached motion effects.",
    ],
    "running": [
        "Show an active work loop, hurry, patrol, pursuit, forward rush, or in-place motion loop appropriate to the selected action style.",
        "Do not draw speed lines, dust clouds, floor shadows, motion trails, or detached motion effects.",
    ],
}

BASE_SPRITE_CONTRACT = (
    "Codex pet sprite contract: original character or object-persona, full-body or full-object "
    "readable inside a 192x208 cell, strong silhouette, clear expression language, stable palette, "
    "consistent proportions, no scenery, no UI, no text, no shadows on a floor, no broad glow haze, "
    "no motion blur, and no detached effects that cross frame slots."
)

ART_STYLE_PRESETS = {
    "pixel-art": {
        "label": "Pixel Art",
        "visual_language": "crisp pixel-art sprite with visible stepped edges, chunky simplified forms, limited palette, and dark 1-2 px outline",
        "codex_safe_translation": "Use clean hard-edged pixel clusters and flat cel shading; avoid tiny dithering that disappears at pet size.",
        "allowed_traits": "blocky highlights, small readable clusters, palette swaps, simple expression pixels, compact attached effects",
        "banned_traits": "painterly blending, anti-aliased glossy edges, noisy dithering, micro-details, realistic texture, text, scenery",
    },
    "stylized-3d": {
        "label": "Stylized 3D Cartoon",
        "visual_language": "stylized 3D-cartoon-inspired avatar with rounded toy-like proportions, clean simplified volumes, and friendly readable face",
        "codex_safe_translation": "Render as a flat sprite strip with 3D-inspired shape cues only; keep lighting simple and consistent across frames.",
        "allowed_traits": "rounded forms, simple rim accents, soft-looking but opaque shapes, chunky limbs/props, clean material blocks",
        "banned_traits": "camera perspective changes, realistic rendering, studio background, cast shadows, complex reflections, depth-of-field blur",
    },
    "soft-clay": {
        "label": "Soft Clay Avatar",
        "visual_language": "soft clay-like avatar with matte rounded forms, handmade charm, simple face, and tactile chunky silhouette",
        "codex_safe_translation": "Suggest clay through rounded shapes and subtle matte color steps while keeping sprite edges clean and extractable.",
        "allowed_traits": "soft rounded blobs, gentle matte color steps, handmade asymmetry, simple accessory shapes, compact attached effects",
        "banned_traits": "realistic clay fingerprints, heavy studio lighting, floor shadows, photographic render background, soft transparent glows",
    },
    "anime": {
        "label": "Anime Sprite",
        "visual_language": "anime-inspired compact sprite with expressive eyes, simplified hair/cloth shapes, sharp pose language, and clean cel shading",
        "codex_safe_translation": "Translate anime into a readable chibi or compact sprite; keep details broad and avoid cinematic key-art composition.",
        "allowed_traits": "large expressive face, simplified hair masses, cel-shaded outfit blocks, crisp attached magic or emotion marks",
        "banned_traits": "full anime illustration, speed-line backgrounds, manga panels, tiny costume filigree, cinematic camera cuts, text bubbles",
    },
    "custom": {
        "label": "Custom",
        "visual_language": "custom compact Codex pet sprite style guided by the user notes",
        "codex_safe_translation": "Apply user style notes only when they preserve the fixed Codex sprite contract and readable 192x208 cells.",
        "allowed_traits": "user-specified traits that remain compact, opaque, hard-edged, and consistent across rows",
        "banned_traits": "anything that breaks transparency, slot boundaries, character consistency, or tiny-pet readability",
    },
}

ACTION_STYLE_PRESETS = {
    "fighter": {
        "label": "Fighter Moves",
        "description": "Arcade fighter energy: stances, dashes, taunts, hit reactions, rushes, and finishers.",
        "states": {
            "idle": "combat stance breathing loop with guard up and small weight shifts",
            "running-right": "rightward fighting-game dash loop",
            "running-left": "leftward fighting-game dash loop",
            "waving": "taunt or stance flourish with gesture and return",
            "jumping": "fighting leap with anticipation, lift, aerial peak, descent, settle",
            "failed": "hit-stun, KO, or defeated reaction",
            "waiting": "charge-up or power idle loop",
            "running": "forward rush or in-place attack run loop",
            "review": "special power or finisher loop",
        },
    },
    "superhero": {
        "label": "Superhero Moves",
        "description": "Heroic poses, cape/energy beats, rescue-ready motion, and triumphant power moments.",
        "states": {
            "idle": "heroic ready stance, cape/cloth lift, chest emblem or motif subtly pulsing",
            "running-right": "rightward heroic sprint, flight glide, or power-assisted dash",
            "running-left": "leftward heroic sprint, flight glide, or power-assisted dash",
            "waving": "hero greeting, salute, confident point, or cape flourish",
            "jumping": "hero takeoff, hover, leap, or landing-ready aerial pose",
            "failed": "hero stagger, cape droop, dimmed emblem, or kneeling recovery",
            "waiting": "power-up anticipation with contained energy around body, hands, emblem, or prop",
            "running": "urgent rescue rush, patrol loop, or forward charge",
            "review": "signature heroic power pose, contained burst, emblem glow, or victory reveal",
        },
    },
    "cozy": {
        "label": "Cozy Companion",
        "description": "Gentle, friendly motions with soft emotional beats and low-intensity charm.",
        "states": {
            "idle": "calm breathing, blink, sway, tiny bounce, or sleepy hover",
            "running-right": "rightward toddle, scamper, float, roll, or gentle glide",
            "running-left": "leftward toddle, scamper, float, roll, or gentle glide",
            "waving": "friendly wave, shy hello, small bow, sparkle-free charm, or happy wiggle",
            "jumping": "small hop, buoyant bob, excited pop-up, or floaty lift",
            "failed": "sad slump, sleepy droop, startled blink, wilt, or tiny wobble",
            "waiting": "listening, thinking, idle fidget, warm pulse, or patient attention loop",
            "running": "busy little work loop, eager hurry, or in-place trot",
            "review": "happy celebration, delighted glow, bow, tiny spin, or proud reveal",
        },
    },
    "ghostly": {
        "label": "Ghostly Motion",
        "description": "Floaty, spectral, wisp-like movement while staying opaque and easy to extract.",
        "states": {
            "idle": "slow hover, sheet/body sway, blink, wisp pulse, or gentle bob",
            "running-right": "rightward drift, glide, phase-like float, or bobbing travel",
            "running-left": "leftward drift, glide, phase-like float, or bobbing travel",
            "waving": "spectral greeting, shy peek, swirl-in-place, or playful haunting gesture",
            "jumping": "buoyant rise, pop-up float, vanish-and-return pose beat, or airy lift",
            "failed": "faded slump, startled poof, dimmed face, or drooping wisp reaction",
            "waiting": "quiet hovering attention, contained mist pulse, or listening loop",
            "running": "eager haunt patrol, quick float loop, or in-place drifting motion",
            "review": "spooky reveal, contained wisp flare, moonlit charm, or playful spectral flourish",
        },
    },
    "magical": {
        "label": "Magical Spirit",
        "description": "Spells, rituals, charms, transformations, and contained magical effects.",
        "states": {
            "idle": "mystic idle, breathing, blink, wand/prop hum, or motif shimmer",
            "running-right": "rightward enchanted glide, scamper, dash, or charm-assisted travel",
            "running-left": "leftward enchanted glide, scamper, dash, or charm-assisted travel",
            "waving": "spell gesture, charm flourish, wand/hand motion, or ritual greeting",
            "jumping": "levitation hop, magic lift, transformation beat, or aerial spell-ready pose",
            "failed": "spell fizzles, startled recoil, dimmed aura, or tired slump",
            "waiting": "spell charge, quiet ritual, listening to magic, or contained aura loop",
            "running": "urgent spellcasting loop, active ritual motion, or pursuit with attached magic",
            "review": "signature spell reveal, transformation, contained aura bloom, or magical celebration",
        },
    },
    "utility": {
        "label": "Utility / Work Loop",
        "description": "Helpful assistant motions, tool use, patrol, focus, and productive activity.",
        "states": {
            "idle": "focused idle, blink, tool-ready stance, screen/face pulse, or attentive breathing",
            "running-right": "rightward purposeful travel, roll, hover, walk, or task dash",
            "running-left": "leftward purposeful travel, roll, hover, walk, or task dash",
            "waving": "acknowledgement gesture, ready signal, tool flourish, or friendly check-in",
            "jumping": "quick hop, tool reach, pop-up notification beat, or active reposition",
            "failed": "error wobble, tired slump, dimmed display, tool drop, or confused blink",
            "waiting": "thinking, scanning, loading, listening, charging, or standby loop",
            "running": "busy work loop, typing/tooling motion, patrol, or focused task cycle",
            "review": "task complete flourish, check-ready reveal, success pulse, or proud presentation",
        },
    },
    "custom": {
        "label": "Custom Actions",
        "description": "Generic Codex-safe row actions intended to be overridden with --state-action or --action-notes.",
        "states": {state: purpose for state, _row, _frames, purpose in ROWS},
    },
}

CHROMA_KEY_CANDIDATES = [
    ("magenta", "#FF00FF"),
    ("cyan", "#00FFFF"),
    ("yellow", "#FFFF00"),
    ("blue", "#0000FF"),
    ("orange", "#FF7F00"),
    ("green", "#00FF00"),
]

DEFAULT_PET_NAME = "Sprout"
CANONICAL_BASE_PATH = "references/canonical-base.png"
LAYOUT_GUIDE_DIR = "references/layout-guides"
LAYOUT_GUIDE_SAFE_MARGIN_X = 18
LAYOUT_GUIDE_SAFE_MARGIN_Y = 16


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-")


def display_from_slug(value: str) -> str:
    words = [word for word in re.split(r"[^a-zA-Z0-9]+", value.strip()) if word]
    return " ".join(word.capitalize() for word in words)


def concept_words(value: str) -> list[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "app",
        "based",
        "codex",
        "compact",
        "digital",
        "for",
        "from",
        "in",
        "of",
        "on",
        "pet",
        "ready",
        "small",
        "the",
        "to",
        "with",
    }
    words = [
        word.lower()
        for word in re.findall(r"[a-zA-Z0-9]+", value)
        if word.lower() not in stop_words
    ]
    return words


def infer_name(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    for raw_value in [args.display_name, args.pet_name]:
        value = raw_value.strip()
        if value:
            return value

    if args.pet_id.strip():
        display = display_from_slug(args.pet_id)
        if display:
            return display

    for raw_value in [args.pet_notes, args.description]:
        words = concept_words(raw_value)
        if words:
            return words[0].capitalize()

    for path in reference_paths:
        display = display_from_slug(path.stem)
        if display:
            return display

    return DEFAULT_PET_NAME


def sentence(value: str) -> str:
    value = " ".join(value.strip().split())
    if not value:
        return value
    if value[-1] not in ".!?":
        value += "."
    return value


def infer_description(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    if args.description.strip():
        return sentence(args.description)
    if args.pet_notes.strip():
        return sentence(f"A compact Codex spirit pet: {args.pet_notes}")
    if reference_paths:
        return "A compact Codex spirit pet based on the provided reference image."
    return "A compact original Codex spirit pet ready for sprite animation."


def infer_pet_notes(args: argparse.Namespace, reference_paths: list[Path]) -> str:
    if args.pet_notes.strip():
        return args.pet_notes.strip()
    if args.description.strip():
        return args.description.strip().rstrip(".")
    if reference_paths:
        return "the spirit shown in the reference image(s)"
    return "a compact original Codex spirit pet"


def default_output_dir(pet_id: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return Path.cwd() / "output" / "hatch-spirit-pet" / f"{pet_id}-{timestamp}"


def rel(path: Path, root: Path) -> str:
    return str(path.resolve().relative_to(root.resolve()))


def image_metadata(path: Path) -> dict[str, object]:
    with Image.open(path) as image:
        return {
            "path": str(path),
            "width": image.width,
            "height": image.height,
            "mode": image.mode,
            "format": image.format,
        }


def draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    fill: str,
    dash: int = 8,
    gap: int = 6,
) -> None:
    x1, y1 = start
    x2, y2 = end
    if x1 == x2:
        step = dash + gap
        for y in range(min(y1, y2), max(y1, y2), step):
            draw.line((x1, y, x2, min(y + dash, max(y1, y2))), fill=fill)
        return
    if y1 == y2:
        step = dash + gap
        for x in range(min(x1, x2), max(x1, x2), step):
            draw.line((x, y1, min(x + dash, max(x1, x2)), y2), fill=fill)
        return
    raise ValueError("draw_dashed_line only supports horizontal or vertical lines")


def create_layout_guide(path: Path, state: str, frames: int) -> dict[str, object]:
    width = frames * ATLAS["cell_width"]
    height = ATLAS["cell_height"]
    cell_width = ATLAS["cell_width"]
    image = Image.new("RGB", (width, height), "#f7f7f7")
    draw = ImageDraw.Draw(image)

    for index in range(frames):
        left = index * cell_width
        right = left + cell_width - 1
        draw.rectangle((left, 0, right, height - 1), outline="#111111", width=2)

        safe_left = left + LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_top = LAYOUT_GUIDE_SAFE_MARGIN_Y
        safe_right = right - LAYOUT_GUIDE_SAFE_MARGIN_X
        safe_bottom = height - 1 - LAYOUT_GUIDE_SAFE_MARGIN_Y
        draw.rectangle(
            (safe_left, safe_top, safe_right, safe_bottom),
            outline="#2f80ed",
            width=2,
        )

        center_x = left + cell_width // 2
        center_y = height // 2
        draw_dashed_line(
            draw,
            (center_x, safe_top),
            (center_x, safe_bottom),
            fill="#b8b8b8",
        )
        draw_dashed_line(
            draw,
            (safe_left, center_y),
            (safe_right, center_y),
            fill="#b8b8b8",
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return {
        "state": state,
        "path": str(path),
        "width": width,
        "height": height,
        "frames": frames,
        "cell_width": ATLAS["cell_width"],
        "cell_height": ATLAS["cell_height"],
        "safe_margin_x": LAYOUT_GUIDE_SAFE_MARGIN_X,
        "safe_margin_y": LAYOUT_GUIDE_SAFE_MARGIN_Y,
        "usage": "layout guide input only; do not copy visible guide lines into generated sprite strips",
    }


def create_layout_guides(run_dir: Path) -> list[dict[str, object]]:
    guide_dir = run_dir / LAYOUT_GUIDE_DIR
    return [
        create_layout_guide(guide_dir / f"{state}.png", state, frames)
        for state, _row, frames, _purpose in ROWS
    ]


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise SystemExit(f"invalid chroma key color: {value}; expected #RRGGBB")
    return tuple(int(value[index : index + 2], 16) for index in (1, 3, 5))


def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def color_distance(left: tuple[int, int, int], right: tuple[int, int, int]) -> float:
    return math.sqrt(sum((left[index] - right[index]) ** 2 for index in range(3)))


def sampled_reference_pixels(paths: list[Path]) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    for path in paths:
        with Image.open(path) as opened:
            image = opened.convert("RGBA")
            image.thumbnail((128, 128), Image.Resampling.LANCZOS)
            data = image.tobytes()
            for index in range(0, len(data), 4):
                red, green, blue, alpha = data[index : index + 4]
                if alpha <= 16:
                    continue
                pixels.append((red, green, blue))

    non_background = [
        pixel
        for pixel in pixels
        if not (pixel[0] > 244 and pixel[1] > 244 and pixel[2] > 244)
    ]
    return non_background or pixels


def choose_chroma_key(reference_paths: list[Path], requested: str) -> dict[str, object]:
    if requested.lower() != "auto":
        rgb = parse_hex_color(requested)
        return {
            "hex": rgb_to_hex(rgb),
            "rgb": list(rgb),
            "name": "user-selected",
            "selection": "manual",
        }

    pixels = sampled_reference_pixels(reference_paths)
    if not pixels:
        rgb = parse_hex_color("#FF00FF")
        return {
            "hex": "#FF00FF",
            "rgb": list(rgb),
            "name": "magenta",
            "selection": "fallback",
        }

    scored: list[tuple[float, int, str, tuple[int, int, int]]] = []
    for preference_index, (name, hex_color) in enumerate(CHROMA_KEY_CANDIDATES):
        rgb = parse_hex_color(hex_color)
        distances = sorted(color_distance(rgb, pixel) for pixel in pixels)
        percentile_index = max(0, min(len(distances) - 1, int(len(distances) * 0.01)))
        scored.append((distances[percentile_index], -preference_index, name, rgb))

    score, _preference, name, rgb = max(scored)
    return {
        "hex": rgb_to_hex(rgb),
        "rgb": list(rgb),
        "name": name,
        "selection": "auto",
        "score": round(score, 2),
    }


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def parse_state_actions(values: list[str]) -> dict[str, str]:
    valid_states = {state for state, _row, _frames, _purpose in ROWS}
    overrides: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise SystemExit(
                f"invalid --state-action {value!r}; expected state=action text"
            )
        state, action = value.split("=", 1)
        state = state.strip()
        action = " ".join(action.strip().split())
        if state not in valid_states:
            valid = ", ".join(sorted(valid_states))
            raise SystemExit(f"invalid --state-action state {state!r}; expected one of: {valid}")
        if not action:
            raise SystemExit(f"invalid --state-action for {state!r}; action text is empty")
        overrides[state] = action
    return overrides


def resolve_action_style(args: argparse.Namespace) -> str:
    if args.action_style:
        return args.action_style
    if args.spirit_archetype in ACTION_STYLE_PRESETS:
        return args.spirit_archetype
    return "custom"


def resolved_state_actions(args: argparse.Namespace) -> dict[str, str]:
    preset = ACTION_STYLE_PRESETS[args.action_style]["states"]
    return {
        state: args.state_actions.get(state) or preset[state]
        for state, _row, _frames, _purpose in ROWS
    }


def resolved_style_notes(args: argparse.Namespace) -> str:
    raw_style_notes = args.style_notes.strip()
    preset = ART_STYLE_PRESETS[args.art_style]
    def clause(label: str, value: str) -> str:
        return f"{label}: {value.rstrip('.')}."

    parts = [
        BASE_SPRITE_CONTRACT,
        clause("Art style", preset["label"]),
        clause("Visual language", preset["visual_language"]),
        clause("Codex-safe translation", preset["codex_safe_translation"]),
        clause("Allowed traits", preset["allowed_traits"]),
        clause("Banned traits", preset["banned_traits"]),
    ]
    if not raw_style_notes:
        return " ".join(parts)
    return " ".join([*parts, f"Additional user style notes: {raw_style_notes}."])


def base_pet_prompt(args: argparse.Namespace) -> str:
    pet_notes = args.pet_notes or "the original spirit shown in the reference image(s)"
    style_notes = resolved_style_notes(args)
    chroma_key = args.chroma_key["hex"]
    chroma_name = args.chroma_key["name"]
    action_notes = args.action_notes.strip() or "Use the selected action style and concept to infer action language for all rows."
    return f"""Create a single clean reference sprite for a Codex app spirit pet named {args.display_name}.

Spirit: {pet_notes}.
Art style preset: {args.art_style}.
Action style preset: {args.action_style}.
Style contract: {style_notes}
Action language: {action_notes}

Use this prompt as an authoritative sprite-production spec. Do not expand it into a polished illustration, painterly character image, anime key art, 3D render, vector mascot, glossy app icon, realistic portrait, or marketing artwork.

Output one centered full-body or full-object signature sprite pose only, on a perfectly flat pure {chroma_name} {chroma_key} chroma-key background. The spirit must be fully visible, readable as a tiny Codex pet, and suitable for animation into a 192x208 sprite cell. The design must be original: do not copy named characters, logos, signature costumes, or exact protected moves. Do not include scenery, text, labels, borders, checkerboard transparency, detached effects, shadows, broad glows, or extra props not present in the reference unless explicitly requested. Do not use {chroma_key}, pure {chroma_name}, or colors close to that chroma key in the spirit, body, object, prop, highlights, or effects."""


def row_prompt(
    args: argparse.Namespace, state: str, row: int, frames: int, purpose: str
) -> str:
    pet_notes = args.pet_notes or "the same original spirit from the approved base reference"
    style_notes = resolved_style_notes(args)
    chroma_key = args.chroma_key["hex"]
    chroma_name = args.chroma_key["name"]
    action_notes = args.action_notes.strip()
    action_notes_text = f"\nUser action notes: {action_notes}." if action_notes else ""
    state_requirements = STATE_REQUIREMENTS.get(state, [])
    state_requirement_text = ""
    if state_requirements:
        state_requirement_text = "\n\nState-specific requirements:\n" + "\n".join(
            f"- {requirement}" for requirement in state_requirements
        )
    transparency_artifact_text = "\n".join(
        f"- {requirement}" for requirement in TRANSPARENCY_ARTIFACT_RULES
    )
    action_preset = ACTION_STYLE_PRESETS[args.action_style]
    return f"""Create a single horizontal sprite strip for the Codex app spirit pet `{args.pet_id}` in the state `{state}`.

Use the attached reference image(s) for spirit identity and the attached base spirit image as the canonical design. Use the attached layout guide image only for frame count, slot spacing, centering, and safe padding. Simplify any high-resolution reference details into the compact 2D spirit pet sprite style. Do not simply copy the still reference pose. Generate distinct animation poses that create a readable cycle.

Identity lock:
- Do not redesign the spirit. Only change pose/action for the `{state}` animation.
- Preserve the exact head/body/object shape, face/expression language, markings, palette, outline weight, proportions, costume/prop/accessory design, motif, and overall silhouette from the canonical base spirit.
- Keep every frame recognizably the same individual spirit, not a related variant.
- If the spirit has a weapon, prop, accessory, object part, or attached effect, preserve its size, side, palette, and attachment style unless the row action requires a small pose-only adjustment.
- Prefer a subtler animation over any change that mutates the spirit identity.

Output exactly {frames} separate animation frames arranged left-to-right in one single row. Each frame must show the same spirit: {pet_notes}.

Art style preset: {args.art_style}.
Action style preset: {args.action_style} ({action_preset['label']}): {action_preset['description']}
Style contract: {style_notes}

Use this prompt as an authoritative sprite-production spec. Do not expand it into a polished illustration, painterly character image, anime key art, 3D render, vector mascot, glossy app icon, realistic portrait, or marketing artwork. The spirit must be original and must not copy any named character, logo, signature costume, or exact protected move.

Animation action: {purpose}.
{action_notes_text}
{state_requirement_text}

Transparency and artifact rules:
{transparency_artifact_text}

Layout requirements:
- Exactly {frames} full-body frames, left to right, in one horizontal row.
- The attached layout guide shows the {frames} frame boxes and inner safe area for this row. Follow its slot count, spacing, centering, and padding.
- Do not reproduce the layout guide itself: no visible boxes, guide lines, center marks, labels, guide colors, or guide background may appear in the output.
- Treat the image as {frames} equal-width invisible frame slots. Fill every slot: each requested slot must contain exactly one complete full-body or full-object spirit pose.
- Spread the {frames} poses evenly across the whole image width. Do not leave any requested slot blank or create large empty gaps between poses.
- Center one complete spirit pose in each slot. No pose or attached effect may cross into the neighboring slot.
- Use a perfectly flat pure {chroma_name} {chroma_key} chroma-key background across the whole image.
- Do not draw visible grid lines, borders, labels, numbers, text, watermarks, or checkerboard transparency.
- Do not include scenery or a background environment.
- Keep the rendering sprite-like: strong silhouette, dark pixel-style outline, limited palette, flat shading, minimal tiny detail.
- Do not use {chroma_key}, pure {chroma_name}, or colors close to that chroma key in the spirit, body, object, props, highlights, shadows, motion marks, dust, landing marks, or effects.
- Do not draw shadows, glows, smears, dust, or landing marks using darker/lighter versions of the chroma-key color.
- Keep every frame self-contained with safe padding. No spirit body/object part, prop, accessory, or attached effect should be clipped by the frame slot.
- Avoid motion blur. Use clear pose changes readable at 192x208.
- Preserve the same silhouette, face/expression language, proportions, palette, costume/prop/accessory, motif, and material across every frame."""


def make_jobs(
    run_dir: Path, copied_refs: list[dict[str, object]]
) -> list[dict[str, object]]:
    reference_inputs = [
        {"path": rel(Path(str(ref["copied_path"])), run_dir), "role": "spirit reference"}
        for ref in copied_refs
    ]
    identity_reference_paths = [CANONICAL_BASE_PATH, "decoded/base.png"]
    jobs: list[dict[str, object]] = [
        {
            "id": "base",
            "kind": "base-pet",
            "status": "pending",
            "prompt_file": "prompts/base-pet.md",
            "input_images": reference_inputs,
            "output_path": "decoded/base.png",
            "depends_on": [],
            "generation_skill": "$imagegen",
            "motion_source": "imagegen",
            "allowed_motion_sources": ["imagegen"],
            "requires_grounded_generation": bool(reference_inputs),
            "allow_prompt_only_generation": not reference_inputs,
            "recording_owner": "parent",
        }
    ]
    for state, _row, frames, _purpose in ROWS:
        depends_on = ["base"]
        extra_inputs: list[dict[str, str]] = []
        mirror_policy: dict[str, object] = {}
        if state == "running-left":
            depends_on.append("running-right")
            extra_inputs.append(
                {
                    "path": "decoded/running-right.png",
                    "role": "rightward gait reference for leftward row decision",
                }
            )
            mirror_policy = {
                "may_derive_from": "running-right",
                "derivation": "horizontal-mirror",
                "requires_explicit_approval": True,
                "fallback_generation_skill": "$imagegen",
            }
        jobs.append(
            {
                "id": state,
                "kind": "row-strip",
                "status": "pending",
                "prompt_file": f"prompts/rows/{state}.md",
                "input_images": [
                    *reference_inputs,
                    {
                        "path": f"{LAYOUT_GUIDE_DIR}/{state}.png",
                        "role": f"layout guide for {frames} frame slots; use for spacing only, do not copy guide lines",
                    },
                    {
                        "path": CANONICAL_BASE_PATH,
                        "role": "canonical identity reference",
                    },
                    {"path": "decoded/base.png", "role": "approved base spirit"},
                    *extra_inputs,
                ],
                "output_path": f"decoded/{state}.png",
                "depends_on": depends_on,
                "generation_skill": "$imagegen",
                "motion_source": "imagegen",
                "allowed_motion_sources": ["imagegen", "video"],
                "requires_grounded_generation": True,
                "allow_prompt_only_generation": False,
                "identity_reference_paths": identity_reference_paths,
                "parallelizable_after": depends_on,
                "mirror_policy": mirror_policy,
                "recording_owner": "parent",
            }
        )
    return jobs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--pet-name",
        default="",
        help="User-facing pet name. Ask the user for this when practical; otherwise choose a short appropriate name.",
    )
    parser.add_argument(
        "--pet-id",
        default="",
        help="Stable pet folder/id slug. Defaults to the slugified pet name.",
    )
    parser.add_argument(
        "--display-name",
        default="",
        help="Display label. Defaults to the pet name.",
    )
    parser.add_argument("--description", default="")
    parser.add_argument("--reference", action="append", default=[])
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--pet-notes", default="")
    parser.add_argument("--style-notes", default="")
    parser.add_argument(
        "--art-style",
        default="pixel-art",
        choices=sorted(ART_STYLE_PRESETS),
        help="Art style preset used to translate the concept into a Codex-safe sprite prompt.",
    )
    parser.add_argument(
        "--action-style",
        default="",
        choices=sorted(ACTION_STYLE_PRESETS),
        help="Action style preset used to map the 9 fixed Codex states to animation actions.",
    )
    parser.add_argument(
        "--state-action",
        action="append",
        default=[],
        metavar="STATE=ACTION",
        help="Override one row action, e.g. --state-action review='heroic power pose'. May be repeated.",
    )
    parser.add_argument(
        "--spirit-archetype",
        default="",
        help="Deprecated compatibility hint. Prefer --art-style and --action-style.",
    )
    parser.add_argument(
        "--action-notes",
        default="",
        help="Optional action mapping notes for rows, e.g. idle=hover, waving=spell, review=celebration.",
    )
    parser.add_argument(
        "--chroma-key",
        default="auto",
        help="Chroma key as #RRGGBB, or auto to choose a safe key from reference colors.",
    )
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    raw_reference_paths = [
        Path(raw_path).expanduser().resolve() for raw_path in args.reference
    ]

    args.display_name = infer_name(args, raw_reference_paths)
    args.pet_name = (args.pet_name or args.display_name).strip()
    args.description = infer_description(args, raw_reference_paths)
    args.pet_notes = infer_pet_notes(args, raw_reference_paths)
    args.pet_id = slugify(args.pet_id or args.pet_name or args.display_name)
    args.action_style = resolve_action_style(args)
    args.state_actions = parse_state_actions(args.state_action)
    if not args.pet_id:
        raise SystemExit("pet id must contain at least one letter or digit")

    run_dir = (
        Path(args.output_dir).expanduser().resolve()
        if args.output_dir
        else default_output_dir(args.pet_id).resolve()
    )
    if run_dir.exists() and any(run_dir.iterdir()) and not args.force:
        raise SystemExit(
            f"{run_dir} already exists and is not empty; pass --force to reuse it"
        )
    run_dir.mkdir(parents=True, exist_ok=True)

    ref_dir = run_dir / "references"
    prompt_dir = run_dir / "prompts"
    row_prompt_dir = prompt_dir / "rows"
    for directory in [
        ref_dir,
        prompt_dir,
        row_prompt_dir,
        run_dir / "decoded",
        run_dir / "qa",
    ]:
        directory.mkdir(parents=True, exist_ok=True)

    copied_refs: list[dict[str, object]] = []
    copied_ref_paths: list[Path] = []
    for index, source in enumerate(raw_reference_paths, start=1):
        if not source.is_file():
            raise SystemExit(f"reference not found: {source}")
        suffix = source.suffix.lower() or ".png"
        copied = ref_dir / f"reference-{index:02d}{suffix}"
        shutil.copy2(source, copied)
        meta = image_metadata(copied)
        meta["source_path"] = str(source)
        meta["copied_path"] = str(copied)
        copied_refs.append(meta)
        copied_ref_paths.append(copied)

    args.chroma_key = choose_chroma_key(copied_ref_paths, args.chroma_key)
    layout_guides = create_layout_guides(run_dir)
    state_actions = resolved_state_actions(args)

    request = {
        "pet_id": args.pet_id,
        "display_name": args.display_name,
        "description": args.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "atlas": ATLAS,
        "rows": [
            {"state": state, "row": row, "frames": frames, "purpose": state_actions[state]}
            for state, row, frames, _purpose in ROWS
        ],
        "layout_guides": [
            {**guide, "path": rel(Path(str(guide["path"])), run_dir)}
            for guide in layout_guides
        ],
        "references": copied_refs,
        "chroma_key": args.chroma_key,
        "pet_notes": args.pet_notes,
        "art_style": args.art_style,
        "art_style_preset": ART_STYLE_PRESETS[args.art_style],
        "action_style": args.action_style,
        "action_style_preset": ACTION_STYLE_PRESETS[args.action_style],
        "state_action_overrides": args.state_actions,
        "state_actions": state_actions,
        "spirit_archetype": args.spirit_archetype,
        "style_notes": args.style_notes,
        "action_notes": args.action_notes,
        "house_style": BASE_SPRITE_CONTRACT,
        "primary_generation_skill": "$imagegen",
    }
    (run_dir / "pet_request.json").write_text(
        json.dumps(request, indent=2) + "\n", encoding="utf-8"
    )

    write_text(prompt_dir / "base-pet.md", base_pet_prompt(args))
    for state, row, frames, _purpose in ROWS:
        write_text(
            row_prompt_dir / f"{state}.md",
            row_prompt(args, state, row, frames, state_actions[state]),
        )

    jobs = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir),
        "primary_generation_skill": "$imagegen",
        "jobs": make_jobs(run_dir, copied_refs),
    }
    (run_dir / "imagegen-jobs.json").write_text(
        json.dumps(jobs, indent=2) + "\n", encoding="utf-8"
    )

    print(
        json.dumps(
            {
                "ok": True,
                "run_dir": str(run_dir),
                "request": str(run_dir / "pet_request.json"),
                "jobs": str(run_dir / "imagegen-jobs.json"),
                "ready_jobs": ["base"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
