#!/usr/bin/env bash
#
# render-diagrams.sh — turn every Mermaid source file into SVG and PNG.
#
# Reads : diagrams/*.mmd
# Writes: images/svg/<name>.svg
#         images/png/<name>.png   (1600x900, dark background)
#
# Usage:
#   ./scripts/render-diagrams.sh              # render every .mmd
#   ./scripts/render-diagrams.sh kafka        # render only files matching "kafka"
#   ./scripts/render-diagrams.sh --check      # fail if any .mmd has no image (CI gate)
#
# Requirements:
#   node >= 18 and npx        (ships with Node)
#   @mermaid-js/mermaid-cli   (installed on demand by npx, ~200 MB first run —
#                              it downloads a headless Chromium)
#
# The hand-authored SVGs listed in images/README.md are NOT overwritten.
# This script skips any target listed in the HAND_AUTHORED array below.

set -euo pipefail

# ---------------------------------------------------------------- paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SRC="${ROOT}/diagrams"
OUT_SVG="${ROOT}/images/svg"
OUT_PNG="${ROOT}/images/png"
THEME="${ROOT}/scripts/mermaid-theme.json"

# Diagrams that a human drew by hand. Never machine-overwrite these.
HAND_AUTHORED=(
  "kafka-architecture"
  "azure-service-bus-architecture"
  "rabbitmq-architecture"
  "broker-decision"
)

BG="#0F1620"     # matches the palette in images/README.md
WIDTH=1600
HEIGHT=900

mkdir -p "${OUT_SVG}" "${OUT_PNG}"

# ---------------------------------------------------------------- helpers
log()  { printf '\033[36m›\033[0m %s\n' "$*"; }
warn() { printf '\033[33m!\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[31m✗\033[0m %s\n' "$*" >&2; exit 1; }

is_hand_authored() {
  local base="$1"
  for h in "${HAND_AUTHORED[@]}"; do
    [[ "${base}" == "${h}" ]] && return 0
  done
  return 1
}

# ---------------------------------------------------------------- --check
# CI gate: every .mmd must have a matching image. Renders nothing.
if [[ "${1:-}" == "--check" ]]; then
  missing=0
  for f in "${SRC}"/*.mmd; do
    base="$(basename "${f}" .mmd)"
    if [[ ! -f "${OUT_SVG}/${base}.svg" ]]; then
      warn "missing image for ${base}.mmd"
      missing=$((missing + 1))
    fi
  done
  [[ ${missing} -eq 0 ]] || die "${missing} diagram(s) have no rendered image. Run ./scripts/render-diagrams.sh"
  log "all diagrams have images"
  exit 0
fi

FILTER="${1:-}"

command -v npx >/dev/null 2>&1 || die "npx not found. Install Node 18+ from https://nodejs.org"

# Write the theme file if it is absent, so colours match the hand-authored SVGs.
if [[ ! -f "${THEME}" ]]; then
  log "writing default theme -> scripts/mermaid-theme.json"
  cat > "${THEME}" <<'JSON'
{
  "theme": "base",
  "themeVariables": {
    "background": "#0F1620",
    "primaryColor": "#141D28",
    "primaryTextColor": "#E8EEF4",
    "primaryBorderColor": "#2A3947",
    "lineColor": "#8FA3B5",
    "secondaryColor": "#1B2634",
    "tertiaryColor": "#141D28",
    "fontFamily": "Inter, Segoe UI, system-ui, sans-serif",
    "fontSize": "15px",
    "clusterBkg": "#131B25",
    "clusterBorder": "#2A3947",
    "edgeLabelBackground": "#0F1620"
  },
  "flowchart": { "curve": "basis", "htmlLabels": true, "padding": 18 },
  "sequence":  { "actorMargin": 60, "width": 190 }
}
JSON
fi

# ---------------------------------------------------------------- render
count=0
skipped=0

shopt -s nullglob
for f in "${SRC}"/*.mmd; do
  base="$(basename "${f}" .mmd)"

  if [[ -n "${FILTER}" && "${base}" != *"${FILTER}"* ]]; then
    continue
  fi

  if is_hand_authored "${base}"; then
    log "skip  ${base}  (hand-authored SVG — edit images/svg/${base}.svg directly)"
    skipped=$((skipped + 1))
    continue
  fi

  log "render ${base}.mmd -> svg + png"

  npx -y @mermaid-js/mermaid-cli \
    --input  "${f}" \
    --output "${OUT_SVG}/${base}.svg" \
    --configFile "${THEME}" \
    --backgroundColor "${BG}" \
    --quiet

  npx -y @mermaid-js/mermaid-cli \
    --input  "${f}" \
    --output "${OUT_PNG}/${base}.png" \
    --configFile "${THEME}" \
    --backgroundColor "${BG}" \
    --width  "${WIDTH}" \
    --height "${HEIGHT}" \
    --scale 2 \
    --quiet

  count=$((count + 1))
done
shopt -u nullglob

# ---------------------------------------------------------------- PNGs from hand-authored SVGs
# mermaid-cli cannot help here — these SVGs were not generated from Mermaid.
# cairosvg is the lightest way to export them. Optional: the SVGs render fine
# on GitHub on their own, PNGs are only needed for LinkedIn and slide decks.
if python -c "import cairosvg" >/dev/null 2>&1; then
  log "exporting hand-authored SVGs to PNG via cairosvg"
  for h in "${HAND_AUTHORED[@]}"; do
    src="${OUT_SVG}/${h}.svg"
    [[ -f "${src}" ]] || continue
    python -c "
import cairosvg
cairosvg.svg2png(url=r'''${src}''',
                 write_to=r'''${OUT_PNG}/${h}.png''',
                 output_width=${WIDTH}, output_height=${HEIGHT},
                 background_color='${BG}')
print('  ${h}.png')
"
  done
else
  warn "cairosvg not installed — hand-authored SVGs were not exported to PNG."
  warn "  pip install cairosvg   then re-run, or skip it: the SVGs work on GitHub."
fi

log "done — ${count} rendered, ${skipped} hand-authored skipped"
log "svg: images/svg/   png: images/png/"
