#!/usr/bin/env bash
#
# check_fonts.sh - Inspect and verify craft-fonts commit hashes across Artcraft specs
#
# Compares %global craft_fonts_commit in each spec against upstream release workflows
# (storytold/<app>/.github/workflows/release.yml), detecting font asset drift when apps
# update to new versions.
#
# Usage:
#   ./check_fonts.sh [--check] [--verbose]
#   ./check_fonts.sh --update [APP...]
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

readonly ALL_APPS=(
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

# Terminal colors
if [[ -t 1 ]]; then
  RED='\033[0;31m'
  GREEN='\033[0;32m'
  YELLOW='\033[1;33m'
  BLUE='\033[0;34m'
  BOLD='\033[1m'
  NC='\033[0m'
else
  RED=''
  GREEN=''
  YELLOW=''
  BLUE=''
  BOLD=''
  NC=''
fi

TIMEOUT="${FETCH_TIMEOUT:-15}"
VERBOSE=0
DO_UPDATE=0
TARGET_APPS=()

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTION] [APP...]

Check and synchronize craft-fonts commit pins between local RPM specs and upstream releases.

Options:
  --check        Check font commits and report status (default)
  --update       Update drifted craft_fonts_commit values in spec files
  --verbose      Display full 40-character commit hashes
  -h, --help     Show this help

Apps:
  ${ALL_APPS[*]}

Environment:
  GITHUB_TOKEN   GitHub Personal Access Token (avoids API/CDN rate limits)
  FETCH_TIMEOUT  Curl timeout in seconds (default: 15)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check)
      DO_UPDATE=0
      shift
      ;;
    --update)
      DO_UPDATE=1
      shift
      ;;
    --verbose)
      VERBOSE=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TARGET_APPS+=("$1")
      shift
      ;;
  esac
done

if [[ "${#TARGET_APPS[@]}" -eq 0 ]]; then
  APPS=("${ALL_APPS[@]}")
else
  APPS=("${TARGET_APPS[@]}")
fi

http_get() {
  local url="$1"
  local -a headers=()
  if [[ -n "${GITHUB_TOKEN:-}" ]]; then
    headers+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  fi
  curl -fsSL --max-time "$TIMEOUT" "${headers[@]}" "$url" 2>/dev/null || return 1
}

COMMON_DEFAULT_FONT=""
fetch_common_default_font() {
  if [[ -n "$COMMON_DEFAULT_FONT" ]]; then
    echo "$COMMON_DEFAULT_FONT"
    return 0
  fi
  local content
  content=$(http_get "https://raw.githubusercontent.com/storytold/craft-common-actions/main/.github/workflows/release.yml" || true)
  COMMON_DEFAULT_FONT=$(echo "$content" | grep -A 5 "craft-fonts-ref:" | grep "default:" | head -n 1 | awk '{print $2}' | tr -d '"' || true)
  echo "$COMMON_DEFAULT_FONT"
}

get_spec_version() {
  local spec="$1"
  [[ -f "$spec" ]] || return 1
  awk '/^[[:space:]]*Version:[[:space:]]*/ { print $2; exit }' "$spec"
}

get_spec_font() {
  local spec="$1"
  [[ -f "$spec" ]] || return 1
  awk '/^[[:space:]]*%global[[:space:]]+craft_fonts_commit[[:space:]]+/ { print $3; exit }' "$spec"
}

get_upstream_font() {
  local app="$1"
  local version="$2"
  local workflow_url="https://raw.githubusercontent.com/storytold/${app}/v${version}/.github/workflows/release.yml"
  local content
  content=$(http_get "$workflow_url" || true)
  if [[ -z "$content" ]]; then
    # Try branch or non-v tag
    workflow_url="https://raw.githubusercontent.com/storytold/${app}/${version}/.github/workflows/release.yml"
    content=$(http_get "$workflow_url" || true)
  fi

  if [[ -z "$content" ]]; then
    return 1
  fi

  local explicit_ref
  explicit_ref=$(echo "$content" | grep "craft-fonts-ref:" | head -n 1 | awk '{print $2}' | tr -d '"' || true)
  if [[ -n "$explicit_ref" ]]; then
    echo "$explicit_ref"
    return 0
  fi

  # Check if it uses craft-common-actions release workflow
  if echo "$content" | grep -q "craft-common-actions"; then
    local default_font
    default_font=$(fetch_common_default_font)
    if [[ -n "$default_font" ]]; then
      echo "$default_font"
      return 0
    fi
  fi

  return 1
}

format_hash() {
  local h="$1"
  if [[ "$VERBOSE" -eq 1 || ${#h} -lt 7 ]]; then
    echo "$h"
  else
    echo "${h:0:7}"
  fi
}

echo -e "${BOLD}Checking Artcraft suite font references...${NC}"
echo ""

DRIFT_COUNT=0
OK_COUNT=0
NA_COUNT=0
ERR_COUNT=0
UPDATED_COUNT=0

if [[ "$VERBOSE" -eq 1 ]]; then
  printf '%-13s %-9s %-42s %-42s %s\n' APP VERSION SPEC_FONT UPSTREAM_FONT STATUS
  printf '%-13s %-9s %-42s %-42s %s\n' \
    '-------------' '---------' '------------------------------------------' '------------------------------------------' '------'
else
  printf '%-13s %-9s %-12s %-15s %s\n' APP VERSION SPEC_FONT UPSTREAM_FONT STATUS
  printf '%-13s %-9s %-12s %-15s %s\n' \
    '-------------' '---------' '------------' '---------------' '------'
fi

for app in "${APPS[@]}"; do
  spec_file="$SCRIPT_DIR/${app}.spec"
  if [[ ! -f "$spec_file" ]]; then
    ((ERR_COUNT++)) || true
    continue
  fi

  spec_ver=$(get_spec_version "$spec_file")
  spec_font=$(get_spec_font "$spec_file" || true)
  upstream_font=$(get_upstream_font "$app" "$spec_ver" || true)

  disp_spec_font="${spec_font:-none}"
  disp_up_font="${upstream_font:-none}"

  status=""
  if [[ -z "$spec_font" ]]; then
    status="${NC}n/a${NC}"
    ((NA_COUNT++)) || true
  elif [[ -z "$upstream_font" ]]; then
    status="${YELLOW}? (unresolved)${NC}"
    ((ERR_COUNT++)) || true
  elif [[ "$spec_font" == "$upstream_font" ]]; then
    status="${GREEN}ok${NC}"
    ((OK_COUNT++)) || true
  else
    status="${RED}${BOLD}DRIFT${NC}"
    ((DRIFT_COUNT++)) || true
    if [[ "$DO_UPDATE" -eq 1 ]]; then
      sed -i -E "s/^([[:space:]]*%global[[:space:]]+craft_fonts_commit[[:space:]]+)[0-9a-fA-F]+/\1${upstream_font}/" "$spec_file"
      status="${GREEN}UPDATED${NC}"
      ((UPDATED_COUNT++)) || true
    fi
  fi

  f_spec=$(format_hash "$disp_spec_font")
  f_up=$(format_hash "$disp_up_font")

  if [[ "$VERBOSE" -eq 1 ]]; then
    printf '%-13s %-9s %-42s %-42s %b\n' "$app" "$spec_ver" "$f_spec" "$f_up" "$status"
  else
    printf '%-13s %-9s %-12s %-15s %b\n' "$app" "$spec_ver" "$f_spec" "$f_up" "$status"
  fi
done

echo ""
echo -e "${BOLD}Summary:${NC}"
echo -e "  In sync (ok):  $OK_COUNT"
echo -e "  Not used (n/a): $NA_COUNT"
if [[ "$DO_UPDATE" -eq 1 ]]; then
  echo -e "  Updated:       $UPDATED_COUNT"
else
  echo -e "  Drifted:       $DRIFT_COUNT"
fi
if [[ "$ERR_COUNT" -gt 0 ]]; then
  echo -e "  Errors:        $ERR_COUNT"
fi

if [[ "$DO_UPDATE" -eq 0 && "$DRIFT_COUNT" -gt 0 ]]; then
  echo ""
  echo -e "${YELLOW}${BOLD}Tip:${NC} Run ${BOLD}./check_fonts.sh --update${NC} to align drifted specs with upstream."
  exit 1
fi

exit 0
