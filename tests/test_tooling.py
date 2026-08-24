from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from tooling import (  # noqa: E402
    MAX_CLAWHUB_BYTES,
    ValidationError,
    build,
    load_project,
    validate_dist,
    validate_generated,
)


class Fixture:
    def __init__(self, parent: Path) -> None:
        self.root = parent / "repo"
        (self.root / "skills/locron").mkdir(parents=True)
        (self.root / "scripts").mkdir()
        (self.root / "VERSION").write_text("0.1.0\n", encoding="utf-8")
        (self.root / "LICENSE").write_text("MIT No Attribution\n", encoding="utf-8")
        (self.root / "catalog.json").write_text(
            json.dumps(
                {
                    "schema": "whitekiwi.skills/v1",
                    "repository": "https://github.com/whitekiwi/skills",
                    "publisher": {"name": "WhiteKiwi", "url": "https://github.com/whitekiwi"},
                    "marketplace": {"name": "whitekiwi-skills", "display_name": "WhiteKiwi Skills"},
                    "skills": {
                        "locron": {
                            "display_name": "Locron",
                            "short_description": "Safely operate Locron schedules.",
                            "category": "Productivity",
                            "keywords": ["locron"],
                            "clawhub": {"slug": "locron", "name": "Locron", "topics": ["scheduler"]},
                        }
                    },
                }
            )
            + "\n",
            encoding="utf-8",
        )
        self.skill = self.root / "skills/locron/SKILL.md"
        self.skill.write_text(
            "---\nname: locron\ndescription: Operate Locron safely when a user asks about Locron jobs.\nlicense: MIT-0\n---\n\n# Locron\n\nInspect first.\n",
            encoding="utf-8",
        )
        (self.root / "skills/locron/agents").mkdir()
        (self.root / "skills/locron/agents/openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Locron"\n'
            '  short_description: "Safely operate Locron schedules."\n'
            '  default_prompt: "Use $locron to explain why this Locron job did not run."\n',
            encoding="utf-8",
        )


class ValidationFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.fixture = Fixture(Path(self.temp.name))

    def tearDown(self) -> None:
        self.temp.cleanup()

    def assert_failure(self, phrase: str) -> None:
        with self.assertRaisesRegex(ValidationError, phrase):
            load_project(self.fixture.root)

    def test_bad_frontmatter_fails_specifically(self) -> None:
        self.fixture.skill.write_text("name: locron\n", encoding="utf-8")
        self.assert_failure("invalid YAML frontmatter")

    def test_broken_link_fails_specifically(self) -> None:
        with self.fixture.skill.open("a", encoding="utf-8") as output:
            output.write("[missing](references/missing.md)\n")
        self.assert_failure("broken relative reference")

    def test_path_escape_fails_specifically(self) -> None:
        with self.fixture.skill.open("a", encoding="utf-8") as output:
            output.write("[escape](../outside.md)\n")
        self.assert_failure("path containment violation")

    def test_non_executable_script_fails_specifically(self) -> None:
        scripts = self.fixture.root / "skills/locron/scripts"
        scripts.mkdir()
        script = scripts / "helper.sh"
        script.write_text("#!/bin/sh\n", encoding="utf-8")
        with self.fixture.skill.open("a", encoding="utf-8") as output:
            output.write("Run `scripts/helper.sh`.\n")
        self.assert_failure("script is not executable")

    def test_stale_openai_metadata_fails_specifically(self) -> None:
        metadata = self.fixture.root / "skills/locron/agents/openai.yaml"
        metadata.write_text("interface:\n", encoding="utf-8")
        self.assert_failure("OpenAI skill metadata differs")

    def test_size_limit_fails_specifically(self) -> None:
        assets = self.fixture.root / "skills/locron/assets"
        assets.mkdir()
        with (assets / "large.bin").open("wb") as output:
            output.truncate(MAX_CLAWHUB_BYTES + 1)
        self.assert_failure("exceeds 50MB")

    def test_version_manifest_mismatch_is_generated_drift(self) -> None:
        build(self.fixture.root, self.fixture.root / "dist")
        (self.fixture.root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "generated file drift"):
            validate_generated(self.fixture.root)

    def test_build_refuses_to_replace_unmarked_directory(self) -> None:
        dist = self.fixture.root / "dist"
        dist.mkdir()
        (dist / "keep.txt").write_text("user data\n", encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "unmarked dist directory"):
            build(self.fixture.root, dist)
        self.assertEqual((dist / "keep.txt").read_text(encoding="utf-8"), "user data\n")


class BuildTests(unittest.TestCase):
    def test_two_builds_are_byte_identical_and_platform_specific(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            first = fixture.root / "first"
            second = fixture.root / "second"
            build(fixture.root, first)
            build(fixture.root, second)
            first_files = {path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()}
            second_files = {path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()}
            self.assertEqual(first_files, second_files)
            validate_dist(fixture.root, first)
            version = (fixture.root / "VERSION").read_text().strip()
            with zipfile.ZipFile(first / f"locron-claude-{version}.zip") as archive:
                names = archive.namelist()
                self.assertTrue(any("/.claude-plugin/plugin.json" in name for name in names))
                self.assertFalse(any("/.codex-plugin/plugin.json" in name for name in names))
            with zipfile.ZipFile(first / f"locron-skill-{version}.zip") as archive:
                self.assertFalse(any("plugin.json" in name for name in archive.namelist()))


if __name__ == "__main__":
    unittest.main()
