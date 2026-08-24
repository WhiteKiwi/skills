#!/bin/sh
set -eu

script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH='' cd -- "$script_dir/.." && pwd)

exec python3 "$repo_dir/scripts/build.py" --root "$repo_dir" "$@"
