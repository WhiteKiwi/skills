from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from test_tooling import Fixture, ROOT
from tooling import build


@unittest.skipUnless(shutil.which("git"), "release tests require git")
class PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        parent = Path(self.temp.name).resolve()
        self.fixture = Fixture(parent)
        self.fixture.add_pushman()
        self.root = self.fixture.root
        # Keep orchestration tests focused on release selection; packaging is
        # already built and validated in the tooling suite.
        validator = self.root / "scripts/validate.sh"
        validator.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        validator.chmod(0o755)
        build(self.root, self.root / "dist")
        (self.root / ".gitignore").write_text("dist/\n", encoding="utf-8")
        self.git("init", "--quiet")
        self.git("add", ".")
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "-m", "fixture")
        self.git("tag", "locron-v0.1.0")
        self.git("tag", "pushman-v0.3.0")
        self.log = parent / "commands.jsonl"
        self.bin_dir = parent / "bin"
        self.bin_dir.mkdir()
        fake_tool = (
            f"#!{sys.executable}\n"
            "import json, os, sys\n"
            "from pathlib import Path\n"
            "with open(os.environ['TASK_PUBLISH_LOG'], 'a', encoding='utf-8') as output:\n"
            "    output.write(json.dumps([Path(sys.argv[0]).name, *sys.argv[1:]]) + '\\n')\n"
            "if sys.argv[1:3] == ['release', 'view']:\n"
            "    sys.exit(1)\n"
            "sys.exit(int(os.environ.get('TASK_FAKE_LOGIN_EXIT', '0')) if sys.argv[1:2] == ['login'] else 0)\n"
        )
        for name in ("gh", "clawhub"):
            tool = self.bin_dir / name
            tool.write_text(fake_tool, encoding="utf-8")
            tool.chmod(0o755)
        self.env = os.environ.copy()
        self.env["PATH"] = str(self.bin_dir) + os.pathsep + self.env["PATH"]
        self.env["TASK_PUBLISH_LOG"] = str(self.log)
        self.env.pop("CLAWHUB_TOKEN", None)

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-C", str(self.root), "-c", "tag.gpgSign=false", "-c", "commit.gpgSign=false", *args],
            capture_output=True, check=True,
        )

    def run_script(self, script: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(ROOT / "scripts" / script), "--root", str(self.root), *args],
            env=self.env, capture_output=True, text=True, check=False, timeout=15,
        )

    def commands(self) -> list[list[str]]:
        return [json.loads(line) for line in self.log.read_text().splitlines()] if self.log.exists() else []

    def test_release_uses_only_tagged_skill_assets_and_clawhub_payload_with_multiple_head_tags(self) -> None:
        self.env["CLAWHUB_TOKEN"] = "fixture-token"
        result = self.run_script("publish.py", "--release", "--tag", "locron-v0.1.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        created = next(command for command in commands if command[:3] == ["gh", "release", "create"])
        self.assertEqual(created[3], "locron-v0.1.0")
        assets = {Path(path).name for path in created[4:created.index("--repo")]}
        self.assertEqual(assets, {
            "locron-claude-0.1.0.zip", "locron-codex-0.1.0.zip",
            "locron-openclaw-0.1.0.zip", "locron-skill-0.1.0.zip", "locron-SHA256SUMS",
        })
        published = [command for command in commands if command[:3] == ["clawhub", "skill", "publish"]]
        self.assertEqual(len(published), 1)
        self.assertEqual(published[0][3], str(self.root / "platforms/openclaw/locron"))
        self.assertEqual(published[0][published[0].index("--version") + 1], "0.1.0")
        self.assertNotIn("--dry-run", published[0])

    def test_failed_login_does_not_expose_token_or_attempt_registry_publication(self) -> None:
        self.env["CLAWHUB_TOKEN"] = "fixture-private-token"
        self.env["TASK_FAKE_LOGIN_EXIT"] = "7"
        result = self.run_script("publish.py", "--release", "--tag", "locron-v0.1.0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("ClawHub login failed with status 7", result.stderr)
        self.assertNotIn("fixture-private-token", result.stdout + result.stderr)
        self.assertFalse(any(command[:3] == ["clawhub", "skill", "publish"] for command in self.commands()))

    def test_manual_clawhub_publication_selects_one_skill_and_its_own_version(self) -> None:
        result = self.run_script("publish.py", "--clawhub", "--skill", "pushman")
        self.assertEqual(result.returncode, 0, result.stderr)
        commands = self.commands()
        self.assertEqual(len(commands), 1)
        self.assertEqual(commands[0][:3], ["clawhub", "skill", "publish"])
        self.assertEqual(commands[0][3], str(self.root / "platforms/openclaw/pushman"))
        self.assertEqual(commands[0][commands[0].index("--version") + 1], "0.3.0")

    def test_all_skill_dry_run_uses_each_catalog_version(self) -> None:
        result = self.run_script("clawhub.py", "--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({
            command[command.index("--slug") + 1]: command[command.index("--version") + 1]
            for command in self.commands()
        }, {"locron": "0.1.0", "pushman": "0.3.0"})
        self.assertTrue(all("--dry-run" in command for command in self.commands()))

    def test_publication_requires_explicit_selection(self) -> None:
        for script, args in (
            ("publish.py", ["--clawhub"]), ("publish.py", ["--release"]),
            ("clawhub.py", ["--publish"]), ("clawhub.py", ["--dry-run", "--version", "0.1.0"]),
        ):
            with self.subTest(script=script, args=args):
                result = self.run_script(script, *args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(self.commands(), [])

    def test_dry_run_can_review_changes_but_publication_rejects_staged_and_unstaged_changes(self) -> None:
        self.fixture.set_version("locron", "0.2.0")
        build(self.root, self.root / "dist")
        result = self.run_script("publish.py", "--dry-run", "--skill", "locron")
        self.assertEqual(result.returncode, 0, result.stderr)
        command = self.commands()[0]
        self.assertIn("--dry-run", command)
        self.assertEqual(command[command.index("--version") + 1], "0.2.0")
        self.log.unlink()
        for staged in (False, True):
            with self.subTest(staged=staged):
                if staged:
                    self.git("add", ".")
                result = self.run_script("publish.py", "--clawhub", "--skill", "locron")
                self.assertEqual(result.returncode, 1)
                self.assertIn("clean committed working tree", result.stderr)
                self.assertEqual(self.commands(), [])

    def test_legacy_unknown_and_mismatched_release_tags_fail_before_external_actions(self) -> None:
        for tag in ("v0.1.0", "unknown-v0.1.0", "locron-v0.3.0"):
            with self.subTest(tag=tag):
                result = self.run_script("publish.py", "--release", "--tag", tag)
                self.assertEqual(result.returncode, 1)
                self.assertIn("release tag must match", result.stderr)
                self.assertEqual(self.commands(), [])

    def test_tag_must_point_to_head(self) -> None:
        self.git("-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "--quiet", "--allow-empty", "-m", "later")
        result = self.run_script("publish.py", "--release", "--tag", "locron-v0.1.0")
        self.assertEqual(result.returncode, 1)
        self.assertIn("to point to HEAD", result.stderr)
        self.assertEqual(self.commands(), [])

    def test_unknown_skill_and_mismatched_clawhub_version_fail_before_external_actions(self) -> None:
        for args in (["--dry-run", "--skill", "unknown"], ["--dry-run", "--skill", "locron", "--version", "0.3.0"]):
            with self.subTest(args=args):
                result = self.run_script("clawhub.py", *args)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(self.commands(), [])


if __name__ == "__main__":
    unittest.main()
