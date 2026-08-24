#!/bin/sh
set -eu

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH='' cd -- "$script_dir/.." && pwd)
scratch_dir=$(mktemp -d "${TMPDIR:-/tmp}/locron-skill-validate.XXXXXX")
trap 'rm -rf "$scratch_dir"' EXIT HUP INT TERM

python3 -m unittest discover -s "$repo_dir/tests" -p 'test_*.py'
if command -v shellcheck >/dev/null 2>&1; then
  shellcheck "$repo_dir"/scripts/*.sh
else
  printf '%s\n' 'note: shellcheck not installed; skipped shell script lint'
fi
python3 "$repo_dir/scripts/build.py" --root "$repo_dir" --dist "$scratch_dir/first"
python3 "$repo_dir/scripts/build.py" --root "$repo_dir" --dist "$scratch_dir/second"
diff -r "$scratch_dir/first" "$scratch_dir/second"
python3 "$repo_dir/scripts/build.py" --root "$repo_dir"
python3 "$repo_dir/scripts/validate.py" --root "$repo_dir" --require-dist

if command -v agentskills >/dev/null 2>&1; then
  agentskills validate "$repo_dir/skills/locron"
else
  printf '%s\n' 'note: skills-ref/agentskills not installed; repository validator remains authoritative'
fi

if command -v claude >/dev/null 2>&1; then
  claude plugin validate "$repo_dir/plugins/locron" --strict
  claude plugin validate "$repo_dir" --strict
else
  printf '%s\n' 'note: Claude Code not installed; skipped additive validator'
fi
