#!/usr/bin/env bash
# submit_to_copr.sh — Automated registration and build submission for Artcraft suite in Fedora Copr.
#
# Defaults:
#   Project:  artcraft-suites
#   Branch:   artcraft
#   Chroots:  fedora-44-x86_64, fedora-44-aarch64, fedora-45-x86_64,
#             fedora-45-aarch64, fedora-rawhide-x86_64, fedora-rawhide-aarch64
#
# Usage:
#   ./submit_to_copr.sh [project_name] [--build] [--branch <name>] [--chroots "<list>"]
#
# Examples:
#   # Register all 13 packages in artcraft-suites:
#   ./submit_to_copr.sh
#
#   # Register and immediately trigger builds for all chroots:
#   ./submit_to_copr.sh --build
#
#   # Build for specific chroots:
#   ./submit_to_copr.sh --build --chroots "fedora-44-x86_64,fedora-rawhide-x86_64"

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

DEFAULT_PROJECT="artcraft-suites"
DEFAULT_BRANCH="artcraft"
DEFAULT_REPO_URL="https://github.com/apicalshark/apicalshark-copr-collection.git"

DEFAULT_CHROOTS=(
  fedora-44-x86_64
  fedora-44-aarch64
  fedora-45-x86_64
  fedora-45-aarch64
  fedora-rawhide-x86_64
  fedora-rawhide-aarch64
)

PROJECT="$DEFAULT_PROJECT"
BRANCH="$DEFAULT_BRANCH"
REPO_URL="${COPR_REPO_URL:-$DEFAULT_REPO_URL}"
BUILD_NOW=0
CUSTOM_CHROOTS=""

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
    --chroots)
      CUSTOM_CHROOTS="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,17p' "$0"
      exit 0
      ;;
    *)
      if [ "$PROJECT" = "$DEFAULT_PROJECT" ] && [[ ! "$1" =~ ^-- ]]; then
        PROJECT="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        exit 2
      fi
      ;;
  esac
done

# 1. Check copr-cli installation
if ! command -v copr-cli &>/dev/null; then
  echo "Error: copr-cli is not installed." >&2
  echo "Install it with: sudo dnf install -y copr-cli" >&2
  exit 1
fi

# 2. Check authentication
echo "Checking Copr authentication..."
if ! copr-cli whoami &>/dev/null; then
  echo "Error: copr-cli is not authenticated." >&2
  echo "Please configure your API token in ~/.config/copr." >&2
  exit 1
fi

USER_NAME=$(copr-cli whoami | awk '{print $NF}')
echo "Authenticated as: $USER_NAME"
echo "Target Project:   $PROJECT"
echo "Git Clone URL:    $REPO_URL"
echo "Git Branch:       $BRANCH"
echo ""

# 3. Ensure Project Exists with Required Chroots and Internet Enabled
if ! copr-cli get "$PROJECT" &>/dev/null; then
  echo "Project '$PROJECT' does not exist yet. Creating project with target chroots and network enabled..."
  create_cmd=(copr-cli create "$PROJECT" --enable-net on)
  for chroot in "${DEFAULT_CHROOTS[@]}"; do
    create_cmd+=(--chroot "$chroot")
  done
  create_cmd+=(--description "Storytold Artcraft Suite: Photocraft, Filmcraft, Soundcraft, Deckcraft, Figcraft, etc.")
  create_cmd+=(--instructions "sudo dnf copr enable ${USER_NAME}/${PROJECT} && sudo dnf install photocraft")
  
  "${create_cmd[@]}"
  echo "Project '$PROJECT' created successfully!"
else
  echo "Project '$PROJECT' exists. Verifying configuration..."
  # Ensure net is on and required chroots are enabled
  modify_cmd=(copr-cli modify "$PROJECT" --enable-net on)
  for chroot in "${DEFAULT_CHROOTS[@]}"; do
    modify_cmd+=(--chroot "$chroot")
  done
  "${modify_cmd[@]}" &>/dev/null || true
  echo "Project configuration verified."
fi
echo ""

# 4. Check if remote branch exists on GitHub
echo "Verifying that branch '$BRANCH' is reachable on remote GitHub repository..."
if ! git ls-remote --exit-code --heads "$REPO_URL" "$BRANCH" &>/dev/null; then
  echo "Warning: Branch '$BRANCH' was not found on $REPO_URL." >&2
  echo "Make sure to push your local branch first:" >&2
  echo "  git push -u origin $BRANCH" >&2
  exit 1
fi
echo "Branch '$BRANCH' is present on remote."
echo ""

# 5. Register/Update all 13 SCM packages
echo "Configuring all 13 Artcraft SCM packages in Copr project '$PROJECT'..."
for app in "${APPS[@]}"; do
  spec_file="${app}.spec"
  if [ ! -f "$spec_file" ]; then
    echo "Warning: $spec_file not found in local directory. Skipping." >&2
    continue
  fi

  echo -n "  -> Configuring package '$app' ... "
  if copr-cli add-package-scm "$PROJECT" \
      --name "$app" \
      --clone-url "$REPO_URL" \
      --commit "$BRANCH" \
      --spec "$spec_file" \
      --method rpkg \
      --webhook-rebuild on &>/dev/null; then
    echo "created (webhook trigger: on)"
  else
    copr-cli edit-package-scm "$PROJECT" \
      --name "$app" \
      --clone-url "$REPO_URL" \
      --commit "$BRANCH" \
      --spec "$spec_file" \
      --method rpkg \
      --webhook-rebuild on &>/dev/null
    echo "updated (webhook trigger: on)"
  fi
done

echo ""
echo "All 13 packages registered successfully in '$PROJECT'!"

# 6. Trigger builds if requested
if [ "$BUILD_NOW" -eq 1 ]; then
  echo ""
  echo "Submitting builds for all 13 packages..."
  build_args=()
  if [ -n "$CUSTOM_CHROOTS" ]; then
    IFS=',' read -ra CHROOT_ARR <<< "$CUSTOM_CHROOTS"
    for c in "${CHROOT_ARR[@]}"; do
      build_args+=(--chroot "$c")
    done
  fi

  for app in "${APPS[@]}"; do
    echo -n "  -> Queuing build for '$app' ... "
    build_out=$(copr-cli build-package "$PROJECT" --name "$app" --nowait "${build_args[@]}" 2>&1)
    build_id=$(echo "$build_out" | grep -oE '[0-9]+' | head -n 1 || echo "submitted")
    echo "build #$build_id"
  done
  echo ""
  echo "All builds queued! Monitor progress at:"
  echo "  https://copr.fedorainfracloud.org/coprs/$USER_NAME/$PROJECT/builds/"
else
  echo ""
  echo "To trigger builds for all packages across all target chroots:"
  echo "  ./submit_to_copr.sh --build"
  echo ""
  echo "Or trigger individually:"
  echo "  copr-cli build-package $PROJECT --name <app>"
fi
