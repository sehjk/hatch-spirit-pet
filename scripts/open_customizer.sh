#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
UI_PATH="$SKILL_DIR/ui/index.html"

if [[ ! -f "$UI_PATH" ]]; then
  echo "Customizer not found: $UI_PATH" >&2
  exit 1
fi

if command -v open >/dev/null 2>&1; then
  open "$UI_PATH"
elif command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$UI_PATH"
else
  printf '%s\n' "$UI_PATH"
fi
