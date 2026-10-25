#!/usr/bin/env bash
#
# check_external_hash.sh - Inspect and verify external asset commit hashes across Artcraft specs
#
# Checks and synchronizes external dependencies pinned by commit SHA:
#   1. craft-fonts: %global craft_fonts_commit vs upstream release workflows
#   2. craft-i18n:  %global craft_i18n_commit vs upstream craft-i18n.rev
#
# Usage:
#   ./check_external_hash.sh [--check] [--verbose]
#   ./check_external_hash.sh --update [APP...]
#   ./check_external_hash.sh --fonts [APP...]
#   ./check_external_hash.sh --i18n [APP...]
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
CHECK_FONTS=1
CHECK_I18N=1
TARGET_APPS=()

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTION] [APP...]

Check and synchronize external commit pins (craft-fonts and craft-i18n) between
local RPM specs and upstream releases.

Options:
  --check        Check commit hashes and report status (default)
  --update       Update drifted commit values in spec files
  --fonts        Only check craft-fonts references
  --i18n         Only check craft-i18n references
  --verbose      Display full 40-character commit hashes
  -h, --help     Show this help

Apps:
  ${ALL_APPS[*]}

Environment:
  GITHUB_TOKEN   GitHub Personal Access Token (avoids API/CDN rate limits)
  FETCH_TIMEOUT  Curl timeout in seconds (default: 15)
EOF
}

# Parse options
FILTER_MODE=0
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
    --fonts)
      CHECK_FONTS=1
      if [[ "$FILTER_MODE" -eq 0 ]]; then
        CHECK_I18N=0
        FILTER_MODE=1
      fi
      shift
      ;;
    --i18n)
      CHECK_I18N=1
      if [[ "$FILTER_MODE" -eq 0 ]]; then
        CHECK_FONTS=0
        FILTER_MODE=1
      fi
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

get_spec_version() {
  local spec="$1"
  [[ -f "$spec" ]] || return 1
  awk '/^[[:space:]]*Version:[[:space:]]*/ { print $2; exit }' "$spec"
}

format_hash() {
  local h="$1"
  if [[ "$VERBOSE" -eq 1 || ${#h} -lt 7 ]]; then
    echo "$h"
  else
    echo "${h:0:7}"
  fi
}

# --- Fonts Helpers ---
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

# --- i18n Helpers ---
get_spec_i18n() {
  local spec="$1"
  [[ -f "$spec" ]] || return 1
  awk '/^[[:space:]]*%global[[:space:]]+craft_i18n_commit[[:space:]]+/ { print $3; exit }' "$spec"
}

get_upstream_i18n() {
  local app="$1"
  local version="$2"
  local rev_url="https://raw.githubusercontent.com/storytold/${app}/v${version}/craft-i18n.rev"
  local content
  content=$(http_get "$rev_url" || true)
  if [[ -z "$content" ]]; then
    rev_url="https://raw.githubusercontent.com/storytold/${app}/${version}/craft-i18n.rev"
    content=$(http_get "$rev_url" || true)
  fi

  if [[ -z "$content" ]]; then
    return 1
  fi

  local clean_rev
  clean_rev=$(tr -d '[:space:]' <<< "$content")
  if [[ "$clean_rev" =~ ^[0-9a-fA-F]{40}$ ]]; then
    echo "$clean_rev"
    return 0
  fi

  return 1
}

# --- Check Runners ---
FONTS_DRIFT_COUNT=0
FONTS_OK_COUNT=0
FONTS_NA_COUNT=0
FONTS_UPDATED_COUNT=0

I18N_DRIFT_COUNT=0
I18N_OK_COUNT=0
I18N_NA_COUNT=0
I18N_UPDATED_COUNT=0

TOTAL_ERR_COUNT=0

if [[ "$CHECK_FONTS" -eq 1 ]]; then
  STEP_LABEL="[1/2]"
  if [[ "$CHECK_I18N" -eq 0 ]]; then
    STEP_LABEL="[1/1]"
  fi
  echo -e "${BOLD}${STEP_LABEL} Checking embedded fonts (craft-fonts)...${NC}"
  echo ""

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
      ((TOTAL_ERR_COUNT++)) || true
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
      ((FONTS_NA_COUNT++)) || true
    elif [[ -z "$upstream_font" ]]; then
      status="${YELLOW}? (unresolved)${NC}"
      ((TOTAL_ERR_COUNT++)) || true
    elif [[ "$spec_font" == "$upstream_font" ]]; then
      status="${GREEN}ok${NC}"
      ((FONTS_OK_COUNT++)) || true
    else
      status="${RED}${BOLD}DRIFT${NC}"
      ((FONTS_DRIFT_COUNT++)) || true
      if [[ "$DO_UPDATE" -eq 1 ]]; then
        sed -i -E "s/^([[:space:]]*%global[[:space:]]+craft_fonts_commit[[:space:]]+)[0-9a-fA-F]+/\1${upstream_font}/" "$spec_file"
        status="${GREEN}UPDATED${NC}"
        ((FONTS_UPDATED_COUNT++)) || true
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
fi

if [[ "$CHECK_I18N" -eq 1 ]]; then
  STEP_LABEL="[2/2]"
  if [[ "$CHECK_FONTS" -eq 0 ]]; then
    STEP_LABEL="[1/1]"
  fi
  echo -e "${BOLD}${STEP_LABEL} Checking embedded translations (craft-i18n)...${NC}"
  echo ""

  if [[ "$VERBOSE" -eq 1 ]]; then
    printf '%-13s %-9s %-42s %-42s %s\n' APP VERSION SPEC_I18N UPSTREAM_I18N STATUS
    printf '%-13s %-9s %-42s %-42s %s\n' \
      '-------------' '---------' '------------------------------------------' '------------------------------------------' '------'
  else
    printf '%-13s %-9s %-12s %-15s %s\n' APP VERSION SPEC_I18N UPSTREAM_I18N STATUS
    printf '%-13s %-9s %-12s %-15s %s\n' \
      '-------------' '---------' '------------' '---------------' '------'
  fi

  for app in "${APPS[@]}"; do
    spec_file="$SCRIPT_DIR/${app}.spec"
    if [[ ! -f "$spec_file" ]]; then
      ((TOTAL_ERR_COUNT++)) || true
      continue
    fi

    spec_ver=$(get_spec_version "$spec_file")
    spec_i18n=$(get_spec_i18n "$spec_file" || true)
    upstream_i18n=$(get_upstream_i18n "$app" "$spec_ver" || true)

    disp_spec_i18n="${spec_i18n:-none}"
    disp_up_i18n="${upstream_i18n:-none}"

    status=""
    if [[ -z "$spec_i18n" && -z "$upstream_i18n" ]]; then
      status="${NC}n/a${NC}"
      ((I18N_NA_COUNT++)) || true
    elif [[ -n "$upstream_i18n" && -z "$spec_i18n" ]]; then
      status="${RED}${BOLD}NEED_ADOPT${NC}"
      ((I18N_DRIFT_COUNT++)) || true
    elif [[ -z "$upstream_i18n" && -n "$spec_i18n" ]]; then
      status="${YELLOW}? (upstream rev missing)${NC}"
      ((TOTAL_ERR_COUNT++)) || true
    elif [[ "$spec_i18n" == "$upstream_i18n" ]]; then
      status="${GREEN}ok${NC}"
      ((I18N_OK_COUNT++)) || true
    else
      status="${RED}${BOLD}DRIFT${NC}"
      ((I18N_DRIFT_COUNT++)) || true
      if [[ "$DO_UPDATE" -eq 1 ]]; then
        sed -i -E "s/^([[:space:]]*%global[[:space:]]+craft_i18n_commit[[:space:]]+)[0-9a-fA-F]+/\1${upstream_i18n}/" "$spec_file"
        status="${GREEN}UPDATED${NC}"
        ((I18N_UPDATED_COUNT++)) || true
      fi
    fi

    f_spec=$(format_hash "$disp_spec_i18n")
    f_up=$(format_hash "$disp_up_i18n")

    if [[ "$VERBOSE" -eq 1 ]]; then
      printf '%-13s %-9s %-42s %-42s %b\n' "$app" "$spec_ver" "$f_spec" "$f_up" "$status"
    else
      printf '%-13s %-9s %-12s %-15s %b\n' "$app" "$spec_ver" "$f_spec" "$f_up" "$status"
    fi
  done
  echo ""
fi

# --- Summary ---
echo -e "${BOLD}Summary:${NC}"
if [[ "$CHECK_FONTS" -eq 1 ]]; then
  if [[ "$DO_UPDATE" -eq 1 ]]; then
    echo -e "  Fonts: in sync ($FONTS_OK_COUNT), n/a ($FONTS_NA_COUNT), updated ($FONTS_UPDATED_COUNT)"
  else
    echo -e "  Fonts: in sync ($FONTS_OK_COUNT), n/a ($FONTS_NA_COUNT), drifted ($FONTS_DRIFT_COUNT)"
  fi
fi
if [[ "$CHECK_I18N" -eq 1 ]]; then
  if [[ "$DO_UPDATE" -eq 1 ]]; then
    echo -e "  i18n:  in sync ($I18N_OK_COUNT), n/a ($I18N_NA_COUNT), updated ($I18N_UPDATED_COUNT)"
  else
    echo -e "  i18n:  in sync ($I18N_OK_COUNT), n/a ($I18N_NA_COUNT), drifted ($I18N_DRIFT_COUNT)"
  fi
fi
if [[ "$TOTAL_ERR_COUNT" -gt 0 ]]; then
  echo -e "  Errors: $TOTAL_ERR_COUNT"
fi

TOTAL_DRIFT=$((FONTS_DRIFT_COUNT + I18N_DRIFT_COUNT))
if [[ "$DO_UPDATE" -eq 0 && "$TOTAL_DRIFT" -gt 0 ]]; then
  echo ""
  echo -e "${YELLOW}${BOLD}Tip:${NC} Run ${BOLD}./check_external_hash.sh --update${NC} to align drifted specs with upstream."
  exit 1
fi

exit 0
