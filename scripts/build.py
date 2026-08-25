#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from tooling import ValidationError, build, validate_dist


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic WhiteKiwi skill packages")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dist", type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    dist = args.dist.resolve() if args.dist else root / "dist"
    try:
        build(root, dist)
        validate_dist(root, dist)
    except (ValidationError, OSError, ValueError) as exc:
        print(f"build failed: {exc}")
        return 1
    print(f"built WhiteKiwi skill artifacts in {dist}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
