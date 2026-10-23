#!/usr/bin/env bash
# fetch_nfpm.sh — Mass fetch upstream packaging/linux/nfpm.yaml for all Artcraft apps.
#
# This script downloads the latest upstream nfpm.yaml configuration for all 13 Artcraft
# suite applications from storytold/<app> into a reference directory so future AI agents
# and maintainers can inspect upstream dependencies, overrides, and packaging metadata.
#
# Usage:
#   ./fetch_nfpm.sh [target_dir]
#
# Default target directory: reference/upstream-nfpm

set -euo pipefail

APPS=(
  photocraft
  pdfcraft
  filmcraft
  wordcraft
  lightcraft
  vectorcraft
  effectcraft
  cadcraft
  gridcraft
  designcraft
  deckcraft
  soundcraft
  figcraft
)

TARGET_DIR="${1:-reference/upstream-nfpm}"
mkdir -p "$TARGET_DIR"

echo "Fetching upstream nfpm.yaml files into $TARGET_DIR/ ..."

for app in "${APPS[@]}"; do
  dest="$TARGET_DIR/${app}-nfpm.yaml"
  url="https://raw.githubusercontent.com/storytold/${app}/main/packaging/linux/nfpm.yaml"
  
  echo -n "  -> Fetching $app ... "
  if curl -fsSL "$url" -o "$dest"; then
    echo "done ($(wc -l < "$dest") lines)"
  else
    echo "FAILED" >&2
  fi
done

echo ""
echo "Successfully fetched nfpm.yaml for ${#APPS[@]} applications into $TARGET_DIR/"
