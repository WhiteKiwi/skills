#!/usr/bin/env python3
"""Validate and publish one independently versioned skill release."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import clawhub
from tooling import ValidationError, archive_names, load_project, select_skills, skill_for_tag


def release(root: Path, catalog: dict[str, Any], tag: str) -> int:
    skill_name = skill_for_tag(catalog, tag)
    info = catalog["skills"][skill_name]
    head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    tagged = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], text=True
    ).strip()
    if tagged != head:
        raise ValidationError(f"release requires tag {tag} to point to HEAD")
    gh = shutil.which("gh")
    if gh is None:
        raise ValidationError("release requires the GitHub CLI (gh)")
    token = os.environ.get("CLAWHUB_TOKEN")
    clawhub_cli = shutil.which("clawhub") if token else None
    if token and clawhub_cli is None:
        raise ValidationError("ClawHub publication requires clawhub on PATH")

    assets = [root / "dist" / name for name in archive_names(skill_name, info["version"])]
    assets.append(root / "dist" / f"{skill_name}-SHA256SUMS")
    if not all(path.is_file() for path in assets):
        raise ValidationError(f"release artifacts are missing for {skill_name}; run ./scripts/build.sh")
    exists = subprocess.run(
        [gh, "release", "view", tag, "--repo", "whitekiwi/skills"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    )
    if exists.returncode == 0:
        print(f"GitHub Release {tag} already exists; leaving it unchanged")
    else:
        notes = (
            f"{info['display_name']} {info['version']}\n\n"
            "Packages for Claude Code, Codex and ChatGPT, OpenClaw, and the portable Agent Skill.\n"
            f"Verify the archives with `{skill_name}-SHA256SUMS`."
        )
        subprocess.run(
            [gh, "release", "create", tag, *(str(path) for path in assets),
             "--repo", "whitekiwi/skills", "--verify-tag", "--title", tag, "--notes", notes],
            check=True,
        )
    if token:
        login = subprocess.run([clawhub_cli, "login", "--token", token], check=False)
        if login.returncode != 0:
            raise ValidationError(f"ClawHub login failed with status {login.returncode}")
        return clawhub.main(["--root", str(root), "--publish", "--skill", skill_name])
    print("CLAWHUB_TOKEN is not configured; skipped ClawHub publication")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--clawhub", action="store_true")
    mode.add_argument("--release", action="store_true")
    parser.add_argument("--skill", help="catalog skill; required for --clawhub, optional for --dry-run")
    parser.add_argument("--tag", help="<skill>-v<version> tag; required for --release")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    if args.release and (not args.tag or args.skill):
        parser.error("--release requires --tag and selects its skill from that tag")
    if not args.release and args.tag:
        parser.error("--tag is only valid with --release")
    if args.clawhub and not args.skill:
        parser.error("--clawhub requires --skill")

    root = args.root.resolve()
    catalog, _ = load_project(root)
    if args.release:
        skill_for_tag(catalog, args.tag)
    else:
        select_skills(catalog, args.skill)
    subprocess.run([str(root / "scripts/validate.sh")], check=True)
    if not args.dry_run:
        changes = subprocess.check_output(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"], text=True
        )
        if changes:
            raise ValidationError("publication requires a clean committed working tree; use --dry-run to review changes")
    if args.release:
        return release(root, catalog, args.tag)
    command = ["--root", str(root), "--publish" if args.clawhub else "--dry-run"]
    if args.skill:
        command.extend(["--skill", args.skill])
    return clawhub.main(command)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValidationError, OSError, subprocess.CalledProcessError) as exc:
        print(f"publication failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
