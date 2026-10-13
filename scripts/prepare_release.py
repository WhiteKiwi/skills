#!/usr/bin/env python3
"""Create an exact per-skill tag for the guarded manual release workflow."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

from tooling import ValidationError, load_project, skill_for_tag


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def prepare(root: Path, tag: str, expected_commit: str) -> None:
    if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch" or os.environ.get("GITHUB_REF") != "refs/heads/main":
        raise ValidationError("manual release must be dispatched from main")
    if not re.fullmatch(r"[0-9a-f]{40}", expected_commit):
        raise ValidationError("expected commit must be an exact lowercase 40-character SHA")
    catalog, _ = load_project(root)
    skill_for_tag(catalog, tag)
    if git(root, "rev-parse", "HEAD") != expected_commit:
        raise ValidationError("checked-out commit differs from expected commit")
    if git(root, "status", "--porcelain", "--untracked-files=all"):
        raise ValidationError("manual release requires a clean committed working tree")
    # Recheck current main after validation; refuse a stale or non-main dispatch.
    git(root, "fetch", "origin", "main")
    if git(root, "rev-parse", "FETCH_HEAD") != expected_commit:
        raise ValidationError("expected commit is no longer the current remote main")
    ref = f"refs/tags/{tag}"
    remote = git(root, "ls-remote", "--tags", "origin", ref, ref + "^{}")
    if remote:
        git(root, "fetch", "origin", f"{ref}:{ref}")
        if git(root, "rev-parse", "FETCH_HEAD^{commit}") != expected_commit:
            raise ValidationError("existing release tag points to a different commit")
        print(f"Verified existing tag {tag} at {expected_commit}")
        return
    # Never force an existing or concurrently-created tag.
    git(root, "tag", tag, expected_commit)
    git(root, "push", "origin", ref)
    if git(root, "ls-remote", "--tags", "origin", ref) != f"{expected_commit}\t{ref}":
        raise ValidationError("published tag did not read back at the expected commit")
    print(f"Created and verified {tag} at {expected_commit}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        prepare(args.root.resolve(), args.tag, args.expected_commit)
    except (ValidationError, OSError, subprocess.CalledProcessError) as exc:
        print(f"release tag preparation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
