#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$SCRIPT_DIR/UI_prototypes"
DIST_DIR="$SCRIPT_DIR/dist"

rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
cp "$SOURCE_DIR"/*.html "$DIST_DIR"/
cp "$SOURCE_DIR"/*.css "$DIST_DIR"/

echo "Frontend prototype built at $DIST_DIR"
