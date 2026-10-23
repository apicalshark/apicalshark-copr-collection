#!/usr/bin/env bash
# trigger_build.sh — Trigger Copr builds from SCM Git using RPM spec files.
#
# Defaults:
#   Project:  artcraft-suites
#   Branch:   artcraft
#   Repo:     https://github.com/apicalshark/apicalshark-copr-collection.git
#   Method:   rpkg
#
# Usage:
#   ./trigger_build.sh [--all] [app_or_spec_names...] [options]
#
# Options:
#   --all                  Trigger builds for all 13 specs in the suite
#   --project <name>       Target Copr project (default: artcraft-suites)
#   --branch <branch>      Git branch/committish (default: artcraft)
#   --repo <url>           Git clone URL (default: repo remote origin)
#   --chroots <list>       Comma-separated chroot filter (e.g. fedora-44-x86_64,fedora-rawhide-x86_64)
#   --watch                Watch the build progress of the triggered build(s)
#   -h, --help             Show this help message
#
# Examples:
#   # Trigger build for a single spec:
#   ./trigger_build.sh photocraft.spec
#
#   # Trigger build for multiple apps:
#   ./trigger_build.sh photocraft filmcraft soundcraft
#
#   # Trigger builds for all 13 apps across all chroots:
#   ./trigger_build.sh --all
#
#   # Trigger build for a specific chroot and watch it:
#   ./trigger_build.sh photocraft --chroots fedora-44-x86_64 --watch

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

DEFAULT_APPS=(
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

DEFAULT_PROJECT="artcraft-suites"
DEFAULT_BRANCH="artcraft"
DEFAULT_REPO_URL="https://github.com/apicalshark/apicalshark-copr-collection.git"

PROJECT="$DEFAULT_PROJECT"
BRANCH="$DEFAULT_BRANCH"
REPO_URL="${COPR_REPO_URL:-$DEFAULT_REPO_URL}"
CHROOT_ARGS=()
WATCH=0
BUILD_ALL=0
SELECTED_TARGETS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --all)
      BUILD_ALL=1
      shift
      ;;
    --project)
      PROJECT="$2"
      shift 2
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --repo)
      REPO_URL="$2"
      shift 2
      ;;
    --chroots|-r)
      IFS=',' read -ra CHR <<< "$2"
      for c in "${CHR[@]}"; do
        CHROOT_ARGS+=(-r "$c")
      done
      shift 2
      ;;
    --watch)
      WATCH=1
      shift
      ;;
    -h|--help)
      sed -n '2,24p' "$0"
      exit 0
      ;;
    *)
      SELECTED_TARGETS+=("$1")
      shift
      ;;
  esac
done

# If no targets specified and not --all, print usage
if [ "$BUILD_ALL" -eq 0 ] && [ "${#SELECTED_TARGETS[@]}" -eq 0 ]; then
  echo "Usage: $0 [--all] [app_or_spec_names...] [options]"
  echo "Try '$0 --help' for options and examples."
  exit 1
fi

# Resolve list of apps to build
BUILD_LIST=()
if [ "$BUILD_ALL" -eq 1 ]; then
  BUILD_LIST=("${DEFAULT_APPS[@]}")
else
  for target in "${SELECTED_TARGETS[@]}"; do
    # Strip path and .spec suffix if present
    app_name=$(basename "$target" .spec)
    BUILD_LIST+=("$app_name")
  done
fi

# 1. Verify copr-cli
if ! command -v copr-cli &>/dev/null; then
  echo "Error: copr-cli is required but not installed." >&2
  echo "Install it with: sudo dnf install -y copr-cli" >&2
  exit 1
fi

# 2. Verify authentication
if ! copr-cli whoami &>/dev/null; then
  echo "Error: copr-cli is not authenticated. Please check ~/.config/copr." >&2
  exit 1
fi

USER_NAME=$(copr-cli whoami | awk '{print $NF}')

# 3. Verify remote branch on GitHub
echo "Verifying branch '$BRANCH' on $REPO_URL..."
if ! git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" &>/dev/null; then
  echo "Error: Branch '$BRANCH' does not exist on remote repository $REPO_URL." >&2
  echo "Please push your branch first: git push -u origin $BRANCH" >&2
  exit 1
fi

echo "Target Project:   $USER_NAME/$PROJECT"
echo "Git Clone URL:    $REPO_URL"
echo "Git Branch:       $BRANCH"
echo "Specs to build:   ${BUILD_LIST[*]}"
echo ""

BUILD_IDS=()

for app in "${BUILD_LIST[@]}"; do
  spec_file="${app}.spec"
  if [ ! -f "$SCRIPT_DIR/$spec_file" ]; then
    echo "Warning: Spec file '$spec_file' not found in $SCRIPT_DIR. Skipping." >&2
    continue
  fi

  echo -n "Triggering SCM build for '$app' ($spec_file) ... "

  # Trigger buildscm with rpkg and network access enabled
  build_out=$(copr-cli buildscm "$PROJECT" \
    --clone-url "$REPO_URL" \
    --commit "$BRANCH" \
    --spec "$spec_file" \
    --method rpkg \
    --enable-net on \
    --nowait \
    "${CHROOT_ARGS[@]}" 2>&1)

  build_id=$(echo "$build_out" | grep -oE '[0-9]+' | head -n 1 || true)

  if [ -n "$build_id" ]; then
    echo "Build ID #$build_id"
    BUILD_IDS+=("$build_id")
  else
    echo "Error triggering build:" >&2
    echo "$build_out" >&2
  fi
done

echo ""
echo "Summary: Triggered ${#BUILD_IDS[@]} build(s)."
echo "Monitor all builds online at:"
echo "  https://copr.fedorainfracloud.org/coprs/$USER_NAME/$PROJECT/builds/"

if [ "$WATCH" -eq 1 ] && [ "${#BUILD_IDS[@]}" -gt 0 ]; then
  echo ""
  echo "Watching build(s): ${BUILD_IDS[*]} ..."
  copr-cli watch-build "${BUILD_IDS[@]}"
fi
