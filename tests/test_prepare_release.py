from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from prepare_release import prepare  # noqa: E402
from tooling import ValidationError  # noqa: E402
from test_tooling import Fixture  # noqa: E402


class ManualReleaseTagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="skills-release-test-")
        self.root = Fixture(Path(self.temp.name)).root
        self.remote = Path(self.temp.name) / "remote.git"
        self.env = patch.dict(os.environ, {"GITHUB_EVENT_NAME": "workflow_dispatch", "GITHUB_REF": "refs/heads/main"})
        self.env.start()
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Release Test")
        self.git("config", "user.email", "release-test@example.invalid")
        self.git("add", ".")
        self.git("commit", "-m", "test: initialize fixture")
        self.sha = self.git("rev-parse", "HEAD")
        self.git("init", "--bare", str(self.remote))
        self.git("remote", "add", "origin", str(self.remote))
        self.git("push", "origin", "main")

    def tearDown(self) -> None:
        self.env.stop()
        self.temp.cleanup()

    def git(self, *args: str) -> str:
        return subprocess.check_output(["git", "-C", str(self.root), *args], text=True, stderr=subprocess.DEVNULL).strip()

    def test_create_read_back_and_idempotent_retry(self) -> None:
        prepare(self.root, "locron-v0.1.0", self.sha)
        self.assertEqual(self.git("ls-remote", "--tags", "origin", "refs/tags/locron-v0.1.0"), f"{self.sha}\trefs/tags/locron-v0.1.0")
        prepare(self.root, "locron-v0.1.0", self.sha)

    def test_rejects_non_main_or_wrong_event_without_creating_a_tag(self) -> None:
        for env in ({"GITHUB_REF": "refs/heads/feature"}, {"GITHUB_EVENT_NAME": "push"}):
            with self.subTest(env=env), patch.dict(os.environ, env):
                with self.assertRaisesRegex(ValidationError, "dispatched from main"):
                    prepare(self.root, "locron-v0.1.0", self.sha)
        self.assertEqual(self.git("tag"), "")

    def test_rejects_wrong_sha_version_and_dirty_tree(self) -> None:
        for tag, sha, error in (("locron-v0.1.0", "main", "exact lowercase"), ("locron-v0.1.0", "0" * 40, "differs"), ("locron-v9.9.9", self.sha, "version")):
            with self.subTest(tag=tag, sha=sha), self.assertRaisesRegex(ValidationError, error):
                prepare(self.root, tag, sha)
        (self.root / "unreviewed.txt").write_text("unreviewed\n")
        with self.assertRaisesRegex(ValidationError, "clean committed"):
            prepare(self.root, "locron-v0.1.0", self.sha)
        self.assertEqual(self.git("tag"), "")

    def test_rejects_stale_remote_main(self) -> None:
        self.git("commit", "--allow-empty", "-m", "test: advance remote")
        self.git("push", "origin", "main")
        self.git("checkout", "--detach", self.sha)
        with self.assertRaisesRegex(ValidationError, "current remote main"):
            prepare(self.root, "locron-v0.1.0", self.sha)
        self.assertEqual(self.git("tag"), "")

    def test_conflicting_tag_is_never_moved(self) -> None:
        self.git("tag", "locron-v0.1.0")
        self.git("push", "origin", "refs/tags/locron-v0.1.0")
        self.git("commit", "--allow-empty", "-m", "test: next commit")
        self.git("push", "origin", "main")
        latest = self.git("rev-parse", "HEAD")
        with self.assertRaisesRegex(ValidationError, "different commit"):
            prepare(self.root, "locron-v0.1.0", latest)
        self.assertEqual(self.git("ls-remote", "--tags", "origin", "refs/tags/locron-v0.1.0"), f"{self.sha}\trefs/tags/locron-v0.1.0")


if __name__ == "__main__":
    unittest.main()
