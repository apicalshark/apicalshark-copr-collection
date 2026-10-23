#!/usr/bin/env bash
# submit_to_copr.sh — Mass-register and submit all 13 Artcraft packages to Fedora Copr.
#
# Requirements:
#   1. copr-cli installed (`sudo dnf install copr-cli`)
#   2. Valid API token configured in ~/.config/copr (get from https://copr.fedorainfracloud.org/api/)
#   3. The Git branch containing the specs must be pushed to GitHub:
#        git push -u origin artcraft
#
# Usage:
#   ./submit_to_copr.sh <copr_project_name> [--build] [--branch <branch_name>]
#
# Examples:
#   # Register all 13 packages under project 'artcraft':
#   ./submit_to_copr.sh artcraft
#
#   # Register and immediately trigger builds:
#   ./submit_to_copr.sh artcraft --build

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

DEFAULT_REPO_URL="https://github.com/apicalshark/apicalshark-copr-collection.git"
REPO_URL="${COPR_REPO_URL:-$DEFAULT_REPO_URL}"
BRANCH="artcraft"
BUILD_NOW=0
PROJECT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --build)
      BUILD_NOW=1
      shift
      ;;
    --branch)
      BRANCH="$2"
      shift 2
      ;;
    --repo)
      REPO_URL="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,17p' "$0"
      exit 0
      ;;
    *)
      if [ -z "$PROJECT" ]; then
        PROJECT="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        exit 2
      fi
      ;;
  esac
done

if [ -z "$PROJECT" ]; then
  echo "Error: Copr project name is required." >&2
  echo "Usage: $0 <project_name> [--build] [--branch <branch>]" >&2
  exit 1
fi

# 1. Check copr-cli installation
if ! command -v copr-cli &>/dev/null; then
  echo "Error: copr-cli is not installed." >&2
  echo "Install it with: sudo dnf install -y copr-cli" >&2
  exit 1
fi

# 2. Check authentication
echo "Checking Copr authentication..."
if ! copr-cli whoami &>/dev/null; then
  echo "Error: copr-cli is not configured or authenticated." >&2
  echo ""
  echo "Please set up your API credentials:"
  echo "  1. Log into https://copr.fedorainfracloud.org/api/"
  echo "  2. Copy the configuration block and paste it into ~/.config/copr"
  echo "  3. Re-run this script."
  exit 1
fi

USER_NAME=$(copr-cli whoami | awk '{print $NF}')
echo "Authenticated as: $USER_NAME"
echo "Target Project:   $PROJECT"
echo "Git Clone URL:    $REPO_URL"
echo "Git Branch:       $BRANCH"
echo ""

# 3. Inform about network access requirement
echo "========================================================================"
echo "IMPORTANT COPR CONFIGURATION REMINDER:"
echo "In Copr Settings -> Build options, ensure 'Enable internet access"
echo "during build' is ON. Cargo needs network access to resolve dependencies."
echo "========================================================================"
echo ""

# 4. Loop through all 13 applications and add/edit SCM package
echo "Registering packages in Copr project '$PROJECT'..."
for app in "${APPS[@]}"; do
  spec_file="${app}.spec"
  if [ ! -f "$spec_file" ]; then
    echo "Warning: $spec_file not found in current directory. Skipping." >&2
    continue
  fi

  echo -n "  -> Configuring package '$app' ... "

  # Try adding package; if it already exists, edit it
  if copr-cli add-package-scm "$PROJECT" \
      --name "$app" \
      --clone-url "$REPO_URL" \
      --commit "$BRANCH" \
      --spec "$spec_file" \
      --method rpkg &>/dev/null; then
    echo "created"
  else
    copr-cli edit-package-scm "$PROJECT" \
      --name "$app" \
      --clone-url "$REPO_URL" \
      --commit "$BRANCH" \
      --spec "$spec_file" \
      --method rpkg &>/dev/null
    echo "updated"
  fi
done

echo ""
echo "All 13 packages registered successfully in Copr project '$PROJECT'!"

# 5. Build packages if requested
if [ "$BUILD_NOW" -eq 1 ]; then
  echo ""
  echo "Submitting builds for all 13 packages..."
  for app in "${APPS[@]}"; do
    echo -n "  -> Queuing build for '$app' ... "
    build_out=$(copr-cli build-package "$PROJECT" --name "$app" --nowait 2>&1)
    build_id=$(echo "$build_out" | grep -oE '[0-9]+' | head -n 1 || echo "submitted")
    echo "build #$build_id"
  done
  echo ""
  echo "All builds queued! Monitor progress at:"
  echo "  https://copr.fedorainfracloud.org/coprs/$USER_NAME/$PROJECT/builds/"
else
  echo ""
  echo "To trigger builds, run:"
  echo "  $0 $PROJECT --build"
  echo "Or trigger individually via:"
  echo "  copr-cli build-package $PROJECT --name <app_name>"
fi
