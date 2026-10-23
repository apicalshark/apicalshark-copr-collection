#!/usr/bin/env bash
# update_specs.sh — Automatically update Artcraft suite RPM specs on upstream release.
#
# Logic:
#   1. Inspects upstream release tags for each of the 13 applications.
#   2. Compares upstream version against local .spec Version.
#   3. If a new version exists:
#      - Downloads upstream packaging/linux/nfpm.yaml at the new release tag.
#      - Compares the new nfpm.yaml against the cached reference in reference/upstream-nfpm/.
#      - If NO nfpm.yaml changes:
#          Automatically updates Version: in the .spec file, resets Release: to 1%{?dist},
#          validates with rpmlint, and updates the cached reference file.
#      - If nfpm.yaml CHANGED:
#          Displays a prominent [ACTION REQUIRED] alert with a diff summary,
#          informing the user or AI agent to review the spec and update dependencies manually.
#
# Usage:
#   ./update_specs.sh [--dry-run] [app_name...]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REFERENCE_DIR="$SCRIPT_DIR/reference/upstream-nfpm"
mkdir -p "$REFERENCE_DIR"

DRY_RUN=0
TARGET_APPS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      TARGET_APPS+=("$1")
      shift
      ;;
  esac
done

ALL_APPS=(
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

if [ "${#TARGET_APPS[@]}" -eq 0 ]; then
  APPS=("${ALL_APPS[@]}")
else
  APPS=("${TARGET_APPS[@]}")
fi

# Terminal colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

fetch_upstream_tag() {
  local app="$1"
  local tag=""

  # Try GitHub API if token available
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    tag=$(curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
      "https://api.github.com/repos/storytold/${app}/releases/latest" 2>/dev/null \
      | grep -m1 '"tag_name":' | cut -d '"' -f 4 || true)
  fi

  # Fallback to git ls-remote (reliable and avoids rate limits)
  if [ -z "$tag" ]; then
    tag=$(git ls-remote --tags --refs "https://github.com/storytold/${app}.git" 2>/dev/null \
      | awk '{print $2}' | sed 's@refs/tags/@@' | grep -E '^v?[0-9]+\.[0-9]+' | sort -Vu | tail -n 1 || true)
  fi

  echo "$tag"
}

fetch_upstream_nfpm() {
  local app="$1"
  local tag="$2"
  local out="$3"

  # Try tag URL first, then fallback to main
  local url="https://raw.githubusercontent.com/storytold/${app}/${tag}/packaging/linux/nfpm.yaml"
  if curl -fsSL "$url" -o "$out" 2>/dev/null; then
    return 0
  fi

  url="https://raw.githubusercontent.com/storytold/${app}/main/packaging/linux/nfpm.yaml"
  curl -fsSL "$url" -o "$out" 2>/dev/null || return 1
}

UPDATED_COUNT=0
MANUAL_COUNT=0
UPTODATE_COUNT=0
ERROR_COUNT=0

echo -e "${BOLD}Checking Artcraft suite for upstream updates...${NC}"
echo ""

for app in "${APPS[@]}"; do
  spec_file="$SCRIPT_DIR/${app}.spec"
  cached_nfpm="$REFERENCE_DIR/${app}-nfpm.yaml"

  if [ ! -f "$spec_file" ]; then
    echo -e "${RED}[ERROR] Spec file not found: $spec_file${NC}" >&2
    ((ERROR_COUNT++)) || true
    continue
  fi

  # Current version in spec
  current_ver=$(grep -E '^[[:space:]]*Version:[[:space:]]*' "$spec_file" | awk '{print $2}' | head -n 1)

  # Upstream latest tag
  upstream_tag=$(fetch_upstream_tag "$app")
  upstream_ver="${upstream_tag#v}"

  if [ -z "$upstream_ver" ]; then
    echo -e "${YELLOW}[WARN] Could not determine upstream version for ${app}.${NC}"
    ((ERROR_COUNT++)) || true
    continue
  fi

  if [ "$current_ver" = "$upstream_ver" ]; then
    echo -e "  ${GREEN}✓${NC} ${BOLD}${app}${NC}: up to date (${current_ver})"
    ((UPTODATE_COUNT++)) || true
    continue
  fi

  echo -e "  ${BLUE}➜${NC} ${BOLD}${app}${NC}: update found (${current_ver} -> ${upstream_ver})"

  # Download new nfpm.yaml to a temporary location
  tmp_nfpm=$(mktemp)
  if ! fetch_upstream_nfpm "$app" "$upstream_tag" "$tmp_nfpm"; then
    echo -e "    ${RED}Failed to fetch upstream nfpm.yaml for ${app}.${NC}"
    rm -f "$tmp_nfpm"
    ((ERROR_COUNT++)) || true
    continue
  fi

  # Check if nfpm.yaml changed
  nfpm_changed=0
  if [ ! -f "$cached_nfpm" ]; then
    nfpm_changed=1
  elif ! cmp -s "$cached_nfpm" "$tmp_nfpm"; then
    nfpm_changed=1
  fi

  if [ "$nfpm_changed" -eq 1 ]; then
    ((MANUAL_COUNT++)) || true
    echo ""
    echo -e "${RED}${BOLD}========================================================================${NC}"
    echo -e "${RED}${BOLD}[ACTION REQUIRED] ${app} packaging/linux/nfpm.yaml HAS CHANGED!${NC}"
    echo -e "${YELLOW}Upstream released ${app} ${upstream_ver} with updated packaging definitions.${NC}"
    echo -e "Please inspect the packaging diff below and update ${BOLD}${app}.spec${NC} accordingly:"
    echo -e "${RED}------------------------------------------------------------------------${NC}"
    if [ -f "$cached_nfpm" ]; then
      diff -u --color=always "$cached_nfpm" "$tmp_nfpm" || true
    else
      echo "No previous reference file existed."
    fi
    echo -e "${RED}------------------------------------------------------------------------${NC}"
    echo -e "Staging new reference file to: ${BOLD}${cached_nfpm}.new${NC}"
    cp "$tmp_nfpm" "${cached_nfpm}.new"
    echo -e "${RED}${BOLD}========================================================================${NC}"
    echo ""
  else
    # No nfpm change -> Safe to auto-update
    ((UPDATED_COUNT++)) || true
    if [ "$DRY_RUN" -eq 1 ]; then
      echo -e "    ${GREEN}[DRY-RUN] Would auto-update ${app}.spec: ${current_ver} -> ${upstream_ver} (no nfpm changes)${NC}"
    else
      # Update Version in spec
      sed -i -E "s/^(Version:[[:space:]]*).*/\1${upstream_ver}/" "$spec_file"
      # Reset Release to 1%{?dist} if modified
      sed -i -E "s/^(Release:[[:space:]]*).*/\11%{?dist}/" "$spec_file"
      
      # Update cached reference
      cp "$tmp_nfpm" "$cached_nfpm"

      # Validate with rpmlint
      if rpmlint "$spec_file" &>/dev/null; then
        echo -e "    ${GREEN}✔ Auto-updated ${app}.spec to ${upstream_ver} (rpmlint passed)${NC}"
      else
        echo -e "    ${YELLOW}⚠ Auto-updated ${app}.spec to ${upstream_ver}, but rpmlint reported warnings/errors.${NC}"
      fi
    fi
  fi

  rm -f "$tmp_nfpm"
done

echo ""
echo -e "${BOLD}Summary:${NC}"
echo -e "  Up-to-date:    $UPTODATE_COUNT"
echo -e "  Auto-updated:  $UPDATED_COUNT"
echo -e "  Manual action: $MANUAL_COUNT"
if [ "$ERROR_COUNT" -gt 0 ]; then
  echo -e "  Errors:        $ERROR_COUNT"
fi

if [ "$MANUAL_COUNT" -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}${BOLD}Note to Maintainers / AI Agents:${NC}"
  echo -e "For packages with [ACTION REQUIRED], review ${BOLD}reference/upstream-nfpm/<app>-nfpm.yaml.new${NC},"
  echo -e "adjust dependencies/build options in <app>.spec, update the reference file, and commit."
  exit 1
fi

exit 0
