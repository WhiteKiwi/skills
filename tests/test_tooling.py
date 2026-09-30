from __future__ import annotations

import json
import os
import shutil
import subprocess
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
                            "version": "0.1.0",
                            "display_name": "Locron",
                            "short_description": "Safely operate Locron schedules.",
                            "category": "Productivity",
                            "homepage": "https://github.com/whitekiwi/locron",
                            "required_bins": ["locron"],
                            "capabilities": ["Scheduling", "Diagnostics"],
                            "default_prompt": "Use $locron to explain why this Locron job did not run.",
                            "default_prompts": ["Safely operate Locron."],
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

    def add_pushman(self) -> None:
        catalog = json.loads((self.root / "catalog.json").read_text(encoding="utf-8"))
        catalog["skills"]["pushman"] = {
            "version": "0.3.0",
            "display_name": "Pushman",
            "short_description": "Safely operate Pushman notifications.",
            "category": "Productivity",
            "homepage": "https://github.com/pushmanhq/pushman-cli",
            "required_bins": ["pushman"],
            "capabilities": ["Notifications", "Diagnostics"],
            "default_prompt": "Use $pushman to inspect Pushman status.",
            "default_prompts": ["Inspect Pushman status."],
            "keywords": ["pushman"],
            "clawhub": {"slug": "pushman", "name": "Pushman", "topics": ["notifications"]},
        }
        (self.root / "catalog.json").write_text(
            json.dumps(catalog) + "\n", encoding="utf-8"
        )
        skill = self.root / "skills/pushman"
        (skill / "agents").mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: pushman\ndescription: Operate Pushman safely when a user asks about Pushman notifications.\nlicense: MIT-0\n---\n\n# Pushman\n\nInspect first.\n",
            encoding="utf-8",
        )
        (skill / "agents/openai.yaml").write_text(
            "interface:\n"
            '  display_name: "Pushman"\n'
            '  short_description: "Safely operate Pushman notifications."\n'
            '  default_prompt: "Use $pushman to inspect Pushman status."\n',
            encoding="utf-8",
        )

    def set_version(self, skill_name: str, version: object) -> None:
        path = self.root / "catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        catalog["skills"][skill_name]["version"] = version
        path.write_text(json.dumps(catalog) + "\n", encoding="utf-8")


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
        self.fixture.set_version("locron", "0.2.0")
        with self.assertRaisesRegex(ValidationError, "generated file drift"):
            validate_generated(self.fixture.root)

    def test_missing_skill_version_fails(self) -> None:
        path = self.fixture.root / "catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        del catalog["skills"]["locron"]["version"]
        path.write_text(json.dumps(catalog), encoding="utf-8")
        self.assert_failure("catalog metadata is incomplete for skill 'locron'")

    def test_invalid_skill_versions_fail(self) -> None:
        for version in (None, 1, "", "v1.2.3", "1.2", "01.2.3", "1.2.3-01", "1.2.3-a..b", "1.2.3+"):
            with self.subTest(version=version):
                self.fixture.set_version("locron", version)
                self.assert_failure("catalog version is not semantic versioning for locron")

    def test_prerelease_and_build_metadata_are_supported(self) -> None:
        self.fixture.set_version("locron", "1.2.3-rc.1+build.001")
        build(self.fixture.root, self.fixture.root / "dist")
        validate_dist(self.fixture.root, self.fixture.root / "dist")

    def test_skill_checksum_cannot_include_another_skill(self) -> None:
        self.fixture.add_pushman()
        dist = self.fixture.root / "dist"
        build(self.fixture.root, dist)
        (dist / "locron-SHA256SUMS").write_bytes((dist / "SHA256SUMS").read_bytes())
        with self.assertRaisesRegex(ValidationError, "skill checksums differ.*locron"):
            validate_dist(self.fixture.root, dist)

    def test_build_refuses_to_replace_unmarked_directory(self) -> None:
        dist = self.fixture.root / "dist"
        dist.mkdir()
        (dist / "keep.txt").write_text("user data\n", encoding="utf-8")
        with self.assertRaisesRegex(ValidationError, "unmarked dist directory"):
            build(self.fixture.root, dist)
        self.assertEqual((dist / "keep.txt").read_text(encoding="utf-8"), "user data\n")


class BuildTests(unittest.TestCase):
    @unittest.skipUnless(os.name == "posix", "direct executable payload check requires POSIX")
    def test_helpers_remain_executable_in_generated_payloads_and_archives(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            script = fixture.root / "skills/locron/scripts/helper.sh"
            script.parent.mkdir()
            script.write_text("#!/bin/sh\nprintf '%s\\n' 'payload works'\n", encoding="utf-8")
            script.chmod(0o755)
            with fixture.skill.open("a", encoding="utf-8") as output:
                output.write("Run `scripts/helper.sh`.\n")
            dist = fixture.root / "dist"
            build(fixture.root, dist)
            validate_dist(fixture.root, dist)
            payloads = [
                fixture.root / "plugins/locron/skills/locron",
                fixture.root / "platforms/openclaw/locron",
                dist / "claude/locron/skills/locron",
                dist / "codex/locron/skills/locron",
                dist / "openclaw/locron",
                dist / "skill/locron",
            ]
            for payload in payloads:
                with self.subTest(payload=payload):
                    result = subprocess.run(
                        [str(payload / "scripts/helper.sh")],
                        capture_output=True, text=True, check=True, timeout=5,
                    )
                    self.assertEqual(result.stdout, "payload works\n")
                    self.assertEqual((payload / "SKILL.md").stat().st_mode & 0o777, 0o644)
            for platform in ("claude", "codex", "openclaw", "skill"):
                with zipfile.ZipFile(dist / f"locron-{platform}-0.1.0.zip") as archive:
                    member = next(info for info in archive.infolist() if info.filename.endswith("/scripts/helper.sh"))
                    self.assertEqual((member.external_attr >> 16) & 0o777, 0o755)
                    self.assertEqual(archive.read(member), script.read_bytes())

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
            catalog, _ = load_project(fixture.root)
            version = catalog["skills"]["locron"]["version"]
            with zipfile.ZipFile(first / f"locron-claude-{version}.zip") as archive:
                names = archive.namelist()
                self.assertTrue(any("/.claude-plugin/plugin.json" in name for name in names))
                self.assertFalse(any("/.codex-plugin/plugin.json" in name for name in names))
            with zipfile.ZipFile(first / f"locron-skill-{version}.zip") as archive:
                self.assertFalse(any("plugin.json" in name for name in archive.namelist()))

    def test_multiple_skills_generate_independent_packages_and_marketplace_entries(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.add_pushman()
            dist = fixture.root / "dist"
            build(fixture.root, dist)
            validate_dist(fixture.root, dist)
            catalog, _ = load_project(fixture.root)
            for skill_name, info in catalog["skills"].items():
                version = info["version"]
                for platform in ("claude", "openclaw", "codex", "skill"):
                    self.assertTrue((dist / f"{skill_name}-{platform}-{version}.zip").is_file())
                for platform in ("claude", "codex"):
                    manifest = json.loads((fixture.root / f"plugins/{skill_name}/.{platform}-plugin/plugin.json").read_text())
                    self.assertEqual(manifest["version"], version)
            marketplace = json.loads(
                (fixture.root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8")
            )
            self.assertEqual(
                {plugin["name"] for plugin in marketplace["plugins"]},
                {"locron", "pushman"},
            )
            claude_marketplace = json.loads((fixture.root / ".claude-plugin/marketplace.json").read_text())
            self.assertEqual(
                {plugin["name"]: plugin["version"] for plugin in claude_marketplace["plugins"]},
                {"locron": "0.1.0", "pushman": "0.3.0"},
            )

    def test_bumping_one_skill_keeps_other_skill_payloads_and_archives_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp))
            fixture.add_pushman()
            first = fixture.root / "first"
            second = fixture.root / "second"
            build(fixture.root, first)
            plugin = fixture.root / "plugins/pushman"
            original_plugin = {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()}
            original_market = json.loads((fixture.root / ".claude-plugin/marketplace.json").read_text())
            fixture.set_version("locron", "0.2.0")
            build(fixture.root, second)
            validate_dist(fixture.root, second)
            self.assertEqual(
                original_plugin,
                {path.relative_to(plugin): path.read_bytes() for path in plugin.rglob("*") if path.is_file()},
            )
            for platform in ("claude", "codex", "openclaw", "skill"):
                name = f"pushman-{platform}-0.3.0.zip"
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())
                self.assertTrue((second / f"locron-{platform}-0.2.0.zip").is_file())
                self.assertFalse((second / f"locron-{platform}-0.1.0.zip").exists())
            self.assertEqual((first / "pushman-SHA256SUMS").read_bytes(), (second / "pushman-SHA256SUMS").read_bytes())
            updated_market = json.loads((fixture.root / ".claude-plugin/marketplace.json").read_text())
            original_entry = next(item for item in original_market["plugins"] if item["name"] == "pushman")
            updated_entry = next(item for item in updated_market["plugins"] if item["name"] == "pushman")
            self.assertEqual(original_entry, updated_entry)


if __name__ == "__main__":
    unittest.main()
