#!/usr/bin/env python3
"""Publish or dry-run generated skills with catalog-owned metadata."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--publish", action="store_true")
    parser.add_argument("--version")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8"))
    repository_version = (root / "VERSION").read_text(encoding="utf-8").strip()
    version = args.version or repository_version
    if version != repository_version:
        raise SystemExit(f"requested ClawHub version {version} != VERSION {repository_version}")
    executable = shutil.which("clawhub")
    if executable is None:
        raise SystemExit("clawhub is not installed")
    for skill_name, info in sorted(catalog["skills"].items()):
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
            version,
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
    raise SystemExit(main())
