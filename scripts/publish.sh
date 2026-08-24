#!/bin/sh
set -eu

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH='' cd -- "$script_dir/.." && pwd)
mode=${1:-}

case "$mode" in
  --dry-run|--release|--clawhub)
    ;;
  *)
    printf '%s\n' 'usage: ./scripts/publish.sh --dry-run | --release | --clawhub' >&2
    exit 2
    ;;
esac

"$repo_dir/scripts/validate.sh"
git -C "$repo_dir" diff --exit-code -- .claude-plugin .agents/plugins plugins platforms/openclaw

version=$(sed -n '1p' "$repo_dir/VERSION")

if [ "$mode" = "--dry-run" ]; then
  exec python3 "$repo_dir/scripts/clawhub.py" --dry-run --version "$version"
fi

if [ "$mode" = "--clawhub" ]; then
  exec python3 "$repo_dir/scripts/clawhub.py" --publish --version "$version"
fi

tag="v$version"
head_tag=$(git -C "$repo_dir" describe --tags --exact-match HEAD 2>/dev/null || true)
if [ "$head_tag" != "$tag" ]; then
  printf 'release requires HEAD tag %s; found %s\n' "$tag" "${head_tag:-none}" >&2
  exit 1
fi
if ! command -v gh >/dev/null 2>&1; then
  printf '%s\n' 'release requires the GitHub CLI (gh)' >&2
  exit 1
fi

if gh release view "$tag" --repo whitekiwi/skills >/dev/null 2>&1; then
  printf 'GitHub Release %s already exists; leaving it unchanged\n' "$tag"
else
  gh release create "$tag" \
    "$repo_dir"/dist/locron-claude-*.zip \
    "$repo_dir"/dist/locron-openclaw-*.zip \
    "$repo_dir"/dist/locron-codex-*.zip \
    "$repo_dir"/dist/locron-skill-*.zip \
    "$repo_dir/dist/SHA256SUMS" \
    --repo whitekiwi/skills \
    --verify-tag \
    --generate-notes \
    --title "$tag"
fi

if [ -n "${CLAWHUB_TOKEN:-}" ]; then
  clawhub login --token "$CLAWHUB_TOKEN"
  python3 "$repo_dir/scripts/clawhub.py" --publish --version "$version"
else
  printf '%s\n' 'CLAWHUB_TOKEN is not configured; skipped ClawHub publication'
fi
