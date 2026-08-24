#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from tooling import ValidationError, validate_all


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the WhiteKiwi skill catalog")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-dist", action="store_true")
    args = parser.parse_args()
    try:
        validate_all(args.root.resolve(), require_dist=args.require_dist)
    except (ValidationError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"validation failed: {exc}")
        return 1
    print("repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
