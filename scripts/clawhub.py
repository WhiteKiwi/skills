#!/usr/bin/env python3
"""Publish or dry-run generated skills with catalog-owned metadata."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from tooling import ValidationError, load_project, select_skills, validate_generated


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skill", help="catalog skill to select; required for publication")
    parser.add_argument("--version")
    args = parser.parse_args(argv)
    if args.publish and not args.skill:
        parser.error("--publish requires --skill")
    if args.version and not args.skill:
        parser.error("--version requires --skill")

    root = args.root.resolve()
    catalog, _ = load_project(root)
    selected = select_skills(catalog, args.skill)
    if args.version and args.version != catalog["skills"][args.skill]["version"]:
        raise ValidationError(f"requested ClawHub version differs from catalog version for {args.skill}")
    validate_generated(root)
    executable = shutil.which("clawhub")
    if executable is None:
        raise ValidationError("clawhub is not installed")
    for skill_name in selected:
        info = catalog["skills"][skill_name]
        clawhub = info["clawhub"]
        command = [
            executable,
            "skill",
            "publish",
            str((root / f"platforms/openclaw/{skill_name}").resolve()),
            "--slug",
            clawhub["slug"],
            "--name",
            clawhub["name"],
            "--version",
            info["version"],
            "--categories",
            info["category"].lower(),
            "--topics",
            ",".join(clawhub["topics"]),
        ]
        if args.dry_run:
            command.extend(["--dry-run", "--json"])
        completed = subprocess.run(command, check=False)
        if completed.returncode != 0:
            return completed.returncode
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError) as exc:
        print(f"ClawHub publication failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
