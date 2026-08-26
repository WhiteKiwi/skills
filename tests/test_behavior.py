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
        positive_capabilities = ("create", "preview", "inspect", "run", "explain", "diagnose", "history", "logs", "service", "dashboard")
        for capability in positive_capabilities:
            self.assertIn(capability, description)
        self.assertIn("generic cron", description)
        self.assertIn("unrelated task managers", description)

        positive_requests = (
            "Create a Locron job that runs my backup hourly.",
            "Preview my Locron weekday schedule in Seoul.",
            "Why did this Locron run fail? Check its history and logs.",
            "Is the Locron daemon service healthy?",
            "Start my local Locron dashboard and show me how to authenticate.",
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

    def test_pushman_description_routes_representative_requests(self) -> None:
        text = (ROOT / "skills/pushman/SKILL.md").read_text(encoding="utf-8")
        description = next(line for line in text.splitlines() if line.startswith("description: ")).removeprefix("description: ").lower()
        for capability in ("send", "inspect", "diagnose", "iphone", "mcp", "login", "pairing", "authorization", "delivery"):
            self.assertIn(capability, description)
        self.assertIn("generic apns/fcm", description)
        self.assertIn("unrelated notification services", description)

        positive_requests = (
            "Use Pushman to notify me when this finishes.",
            "List my Pushman devices and monthly usage.",
            "Why did this Pushman notification fail to deliver?",
            "Log in to Pushman from this headless CLI.",
            "Pair the Pushman CLI with my iPhone.",
            "Configure the local Pushman MCP server.",
        )
        negative_requests = (
            "Implement APNs token registration in this iOS app.",
            "Send this message through Pushover.",
            "Explain Firebase Cloud Messaging topics.",
        )
        for request in positive_requests:
            self.assertIn("pushman", request.lower())
        for request in negative_requests:
            self.assertNotIn("pushman", request.lower())


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


class InstalledPushmanForwardTest(unittest.TestCase):
    @unittest.skipUnless(shutil.which("pushman"), "pushman is not installed")
    def test_version_help_and_mcp_discovery_do_not_send(self) -> None:
        version = subprocess.run(
            ["pushman", "version"], text=True, capture_output=True, check=True
        )
        self.assertIn("pushman ", version.stdout)
        help_result = subprocess.run(
            ["pushman", "help", "mcp"], text=True, capture_output=True, check=True
        )
        self.assertIn("Model Context Protocol", help_result.stdout)

        process = subprocess.Popen(
            ["pushman", "mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None

        def exchange(payload: dict) -> dict:
            process.stdin.write(json.dumps(payload) + "\n")
            process.stdin.flush()
            return json.loads(process.stdout.readline())

        initialized = exchange(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2026-07-28",
                    "capabilities": {},
                    "clientInfo": {"name": "skills-forward-test", "version": "1"},
                },
            }
        )
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "pushman")
        process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        process.stdin.flush()
        listed = exchange({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        tool_names = {tool["name"] for tool in listed["result"]["tools"]}
        self.assertEqual(
            tool_names,
            {
                "pushman_send_notification",
                "pushman_list_devices",
                "pushman_list_history",
                "pushman_get_message",
                "pushman_get_usage",
                "pushman_get_status",
                "pushman_doctor",
            },
        )
        process.stdin.close()
        self.assertEqual(process.wait(timeout=5), 0)
        self.assertEqual(process.stderr.read(), "")
        process.stdout.close()
        process.stderr.close()


if __name__ == "__main__":
    unittest.main()
