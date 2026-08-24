from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class TriggerContractTests(unittest.TestCase):
    def test_description_routes_representative_requests(self) -> None:
        text = (ROOT / "skills/locron/SKILL.md").read_text(encoding="utf-8")
        description = next(line for line in text.splitlines() if line.startswith("description: ")).removeprefix("description: ").lower()
        positive_capabilities = ("create", "preview", "inspect", "run", "explain", "diagnose", "history", "logs", "service")
        for capability in positive_capabilities:
            self.assertIn(capability, description)
        self.assertIn("generic cron", description)
        self.assertIn("unrelated task managers", description)

        positive_requests = (
            "Create a Locron job that runs my backup hourly.",
            "Preview my Locron weekday schedule in Seoul.",
            "Why did this Locron run fail? Check its history and logs.",
            "Is the Locron daemon service healthy?",
            "Dry-run an update to my Locron job.",
        )
        negative_requests = (
            "Explain what the five cron fields mean.",
            "Add this reminder to Todoist.",
            "Debug this systemd timer unit.",
        )
        for request in positive_requests:
            self.assertIn("locron", request.lower())
        for request in negative_requests:
            self.assertNotIn("locron", request.lower())


class InstalledLocronForwardTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("locron"), "locron is not installed")
    def test_read_dry_run_and_read_back_use_only_temporary_state(self) -> None:
        with tempfile.TemporaryDirectory(prefix="locron-skill-forward-") as state:
            env = os.environ.copy()
            env["LOCRON_STATE_DIR"] = state

            def locron(*args: str) -> dict:
                completed = subprocess.run(
                    ["locron", "--format", "json", *args],
                    env=env,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["schema"], "locron.cli/v1")
                self.assertTrue(payload["ok"])
                return payload

            self.assertEqual(locron("list")["data"], [])
            preview = locron("add", "skill-forward-test", "--every", "1h", "--disabled", "--dry-run", "--", "/usr/bin/true")
            self.assertEqual(preview["command"], "add")
            self.assertEqual(locron("list", "--all")["data"], [])
            created = locron("add", "skill-forward-test", "--every", "1h", "--disabled", "--", "/usr/bin/true")
            self.assertEqual(created["command"], "add")
            shown = locron("show", "skill-forward-test")
            self.assertEqual(shown["data"]["name"], "skill-forward-test")
            explain_help = subprocess.run(
                ["locron", "help", "explain"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            if explain_help.returncode == 0:
                explained = locron("explain", "skill-forward-test")
                self.assertEqual(explained["command"], "explain")
                self.assertEqual(explained["data"]["job"]["name"], "skill-forward-test")
            removed = locron("remove", "skill-forward-test")
            self.assertEqual(removed["command"], "remove")


if __name__ == "__main__":
    unittest.main()
