#!/usr/bin/env bash
set -Eeuo pipefail

FRAMES_DIR="${1:-frames}"
OUTPUT="${2:-regenexcalibur_render.mp4}"
FPS="${FPS:-24}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required for local rendering." >&2
  exit 1
fi

if [[ ! -d "$FRAMES_DIR" ]]; then
  echo "Frame directory not found: $FRAMES_DIR" >&2
  exit 2
fi

ffmpeg -y \
  -framerate "$FPS" \
  -i "$FRAMES_DIR/frame_%04d.png" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  "$OUTPUT"

echo "Rendered $OUTPUT"
