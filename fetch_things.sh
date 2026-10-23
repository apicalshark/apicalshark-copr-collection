#!/usr/bin/env bash
#
# fetch_things.sh - inspect upstream releases for the Storytold Artcraft apps
#
# Reports the latest upstream version of each app, compares it with the local
# spec file (when one exists), validates source archive URLs, and downloads
# source archives either through spectool or curl.
#
set -euo pipefail

readonly APPS=(
  photocraft pdfcraft filmcraft wordcraft lightcraft vectorcraft effectcraft
  cadcraft gridcraft designcraft deckcraft soundcraft figcraft
)
readonly OWNER="${GITHUB_OWNER:-storytold}"
readonly TIMEOUT="${FETCH_TIMEOUT:-20}"
readonly DOWNLOAD_TIMEOUT=300

usage() {
  cat <<EOF
Usage: $(basename "$0") [OPTION]

Inspect and fetch upstream releases for the Storytold Artcraft suite.

Options:
  --versions         Show each app's latest upstream version and local spec version
  --check            Validate upstream tags and source archive URLs
  --download [APP...]  Download source archives (all apps when no APP is given)
  -h, --help         Show this help

Apps:
  ${APPS[*]}

Environment:
  GITHUB_TOKEN   Query the GitHub API for release tags (avoids anonymous rate limits)
  GITHUB_OWNER   Upstream GitHub owner (default: storytold)
  FETCH_TIMEOUT  Per-request network timeout in seconds (default: 20)
EOF
}

# Fetch a URL, failing on HTTP errors.
http_get() {
  curl -fsSL --max-time "$TIMEOUT" "$@"
}

# Report whether a name is one of the known apps.
is_app() {
  local app
  for app in "${APPS[@]}"; do
    [[ $app == "$1" ]] && return 0
  done
  return 1
}

# Turn a release tag into a bare version (v0.14.0 -> 0.14.0).
strip_v() {
  printf '%s\n' "${1#v}"
}

# Latest release tag through the GitHub API. Requires GITHUB_TOKEN.
api_latest_tag() {
  local app=$1 json
  local -a headers=(-H 'Accept: application/vnd.github+json')
  [[ -n ${GITHUB_TOKEN:-} ]] &&
    headers+=(-H "Authorization: Bearer ${GITHUB_TOKEN}")

  json=$(http_get "${headers[@]}" \
    "https://api.github.com/repos/${OWNER}/${app}/releases/latest" 2>/dev/null) || return 1
  jq -er '.tag_name // empty' <<<"$json" 2>/dev/null
}

# Latest release tag through git, which is not subject to API rate limits.
git_latest_tag() {
  local app=$1 tags
  tags=$(git ls-remote --tags --refs "https://github.com/${OWNER}/${app}" 2>/dev/null) || return 1
  tags=$(sed 's#.*refs/tags/##' <<<"$tags" | grep -E '^v?[0-9]' | sort -Vu | tail -n 1) || return 1
  [[ -n $tags ]] || return 1
  printf '%s\n' "$tags"
}

# Resolve the latest upstream tag for an app.
latest_tag() {
  local app=$1 tag
  if [[ -n ${GITHUB_TOKEN:-} ]]; then
    tag=$(api_latest_tag "$app") && { printf '%s\n' "$tag"; return 0; }
  fi
  git_latest_tag "$app"
}

# Print the Version field of a local spec, if the spec exists.
spec_version() {
  local spec="$1.spec"
  [[ -f $spec ]] || return 1
  awk '/^Version:[[:space:]]*/ { print $2; exit }' "$spec"
}

# Source archive for a tag; it unpacks to <app>-<version>, matching Source0.
archive_url() {
  local app=$1 tag=$2
  printf 'https://github.com/%s/%s/archive/refs/tags/%s.tar.gz' "$OWNER" "$app" "$tag"
}

cmd_versions() {
  local app tag upstream spec status

  printf '%-13s %-12s %-12s %s\n' APP UPSTREAM SPEC STATUS
  printf '%-13s %-12s %-12s %s\n' \
    '-------------' '------------' '------------' '------'

  for app in "${APPS[@]}"; do
    if tag=$(latest_tag "$app"); then
      upstream=$(strip_v "$tag")
      if spec=$(spec_version "$app"); then
        if [[ $spec == "$upstream" ]]; then
          status=ok
        else
          status="stale"
        fi
      else
        spec=-
        status='no spec'
      fi
    else
      upstream=?
      spec=$(spec_version "$app" || true)
      [[ -n $spec ]] || spec=-
      status=unreachable
    fi
    printf '%-13s %-12s %-12s %s\n' "$app" "$upstream" "$spec" "$status"
  done
}

cmd_check() {
  local app tag upstream url spec status archive failures=0

  printf '%-13s %-12s %-9s %s\n' APP UPSTREAM ARCHIVE SPEC
  printf '%-13s %-12s %-9s %s\n' \
    '-------------' '------------' '---------' '------------'

  for app in "${APPS[@]}"; do
    if ! tag=$(latest_tag "$app"); then
      printf '%-13s %-12s %-9s %s\n' "$app" '?' 'skip' 'unreachable'
      failures=$((failures + 1))
      continue
    fi

    upstream=$(strip_v "$tag")
    url=$(archive_url "$app" "$tag")
    if curl -fsIL --max-time "$TIMEOUT" -o /dev/null "$url" 2>/dev/null; then
      archive=ok
    else
      archive=FAIL
      failures=$((failures + 1))
    fi

    if spec=$(spec_version "$app"); then
      if [[ $spec == "$upstream" ]]; then
        status=ok
      else
        status="drift (${spec})"
        failures=$((failures + 1))
      fi
    else
      status='no spec'
    fi

    printf '%-13s %-12s %-9s %s\n' "$app" "$upstream" "$archive" "$status"
  done

  if ((failures > 0)); then
    printf '\n%d check(s) failed\n' "$failures" >&2
    return 1
  fi
  printf '\nAll checks passed\n'
}

cmd_download() {
  local app tag version url dest tmp
  local -a apps=("$@")
  local rc=0

  ((${#apps[@]})) || apps=("${APPS[@]}")

  for app in "${apps[@]}"; do
    if ! is_app "$app"; then
      printf 'Unknown app: %s\n' "$app" >&2
      rc=2
      continue
    fi

    if [[ -f "$app.spec" ]]; then
      if ! command -v spectool >/dev/null 2>&1; then
        printf '%-13s spectool not found; cannot fetch sources declared in %s.spec\n' \
          "$app" "$app" >&2
        rc=1
        continue
      fi
      printf '%-13s spectool -g -S %s.spec\n' "$app" "$app"
      if ! spectool -g -S "$app.spec"; then
        printf '%-13s source download failed\n' "$app" >&2
        rc=1
      fi
      continue
    fi

    if ! tag=$(latest_tag "$app"); then
      printf '%-13s could not resolve upstream tag\n' "$app" >&2
      rc=1
      continue
    fi

    version=$(strip_v "$tag")
    url=$(archive_url "$app" "$tag")
    dest="${app}-${version}.tar.gz"
    tmp="${dest}.part"

    if [[ -s $dest ]]; then
      printf '%-13s %s already present\n' "$app" "$dest"
      continue
    fi

    printf '%-13s fetching %s\n' "$app" "$dest"
    if curl -fsSL --retry 3 --retry-delay 1 --max-time "$DOWNLOAD_TIMEOUT" \
      -o "$tmp" "$url"; then
      mv "$tmp" "$dest"
    else
      rm -f "$tmp"
      printf '%-13s download failed: %s\n' "$app" "$url" >&2
      rc=1
    fi
  done

  return "$rc"
}

main() {
  case ${1:-} in
    --versions)
      [[ $# -eq 1 ]] || { usage >&2; exit 2; }
      cmd_versions
      ;;
    --check)
      [[ $# -eq 1 ]] || { usage >&2; exit 2; }
      cmd_check
      ;;
    --download)
      shift
      cmd_download "$@"
      ;;
    -h | --help | '')
      usage
      ;;
    *)
      printf 'Unknown option: %s\n\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
}

main "$@"
