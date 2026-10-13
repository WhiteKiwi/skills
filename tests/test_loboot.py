from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from tooling import build, load_project, parse_frontmatter, skill_for_tag, validate_dist  # noqa: E402


class LobootDistributionTests(unittest.TestCase):
    def test_independent_payloads_include_workflow_and_safety_reference(self) -> None:
        # Build a complete temporary checkout to avoid changing the real tree in a test.
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "repo"
            root.mkdir()
            (root / "scripts").mkdir()
            shutil.copyfile(ROOT / "catalog.json", root / "catalog.json")
            shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
            shutil.copytree(ROOT / "skills", root / "skills")
            build(root, root / "dist")
            validate_dist(root, root / "dist")
            catalog, _ = load_project(root)
            info = catalog["skills"]["loboot"]
            self.assertEqual(info["required_bins"], ["loboot"])
            self.assertEqual(skill_for_tag(catalog, f"loboot-v{info['version']}"), "loboot")
            source = root / "skills/loboot"
            for platform in ("claude", "codex", "openclaw", "skill"):
                with self.subTest(platform=platform):
                    archive_path = root / "dist" / f"loboot-{platform}-{info['version']}.zip"
                    with zipfile.ZipFile(archive_path) as archive:
                        prefix = "loboot/skills/loboot/" if platform in ("claude", "codex") else "loboot/"
                        self.assertEqual(archive.read(prefix + "references/safety.md"), (source / "references/safety.md").read_bytes())
                        self.assertEqual(archive.read(prefix + "agents/openai.yaml"), (source / "agents/openai.yaml").read_bytes())
                        entrypoint = archive.read(prefix + "SKILL.md").decode()
                        if platform != "openclaw":
                            self.assertEqual(entrypoint, (source / "SKILL.md").read_text())
                        self.assertTrue(all(name.startswith("loboot/") for name in archive.namelist()))
            metadata, _, _ = parse_frontmatter(root / "platforms/openclaw/loboot/SKILL.md")
            self.assertEqual(metadata["metadata"]["openclaw"]["requires"]["bins"], ["loboot"])
            for path in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
                entries = json.loads((root / path).read_text())["plugins"]
                self.assertEqual(sum(entry["name"] == "loboot" for entry in entries), 1)


@unittest.skipUnless(shutil.which("loboot"), "loboot is not installed; offline CLI forward checks skipped")
class InstalledLobootForwardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="loboot-skill-forward-")
        self.work = Path(self.temp.name).resolve()
        self.binary = shutil.which("loboot")
        self.executable = str(Path(shutil.which("true") or "/usr/bin/true").resolve())

    def tearDown(self) -> None:
        self.temp.cleanup()

    def invoke(self, platform: str, *args: str, ok: bool = True) -> dict:
        result = subprocess.run(
            [self.binary, "--root", str(self.work / platform), "--platform", platform, "--json", *args],
            text=True, capture_output=True, timeout=10,
        )
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "loboot.cli/v1")
        self.assertEqual(payload["ok"], ok, result.stdout + result.stderr)
        self.assertEqual(result.returncode, 0 if ok else 1, result.stderr)
        return payload["data"] if ok else payload["error"]

    def snapshot(self, platform: str) -> dict:
        root = self.work / platform
        return {str(p.relative_to(root)): (p.is_dir(), p.read_bytes() if p.is_file() else None, p.stat().st_mtime_ns)
                for p in root.rglob("*")} if root.exists() else {}

    def add_args(self) -> tuple[str, ...]:
        return ("add", "skill-forward", "--cwd", str(self.work), "--mode", "once", "--restart", "never", "--", self.executable, "$HOME; literal")

    def manifest(self, platform: str) -> Path:
        path = self.work / f"{platform}.toml"
        # JSON strings are valid basic TOML strings for these test values.
        path.write_text("\n".join(f"{key} = {json.dumps(value)}" for key, value in {
            "id": "skill-forward", "executable": self.executable, "args": ["updated"],
            "cwd": str(self.work), "mode": "once", "restart": "never",
        }.items()) + "\n")
        return path

    def test_text_version_and_offline_definition_lifecycle(self) -> None:
        result = subprocess.run([self.binary, "--version", "--json"], text=True, capture_output=True, check=True, timeout=10)
        self.assertTrue(result.stdout.startswith("loboot "))
        for platform in ("linux", "macos"):
            with self.subTest(platform=platform):
                preview = self.invoke(platform, "--dry-run", *self.add_args())
                self.assertTrue(preview["dry_run"])
                self.assertFalse((self.work / platform).exists())
                created = self.invoke(platform, *self.add_args())
                self.assertFalse(created["started"])
                shown = self.invoke(platform, "show", "skill-forward")["service"]
                self.assertEqual(shown["manifest"]["args"], ["$HOME; literal"])
                self.assertEqual(shown["manifest"]["mode"], "once")
                manifest = self.manifest(platform)
                explained = self.invoke(platform, "explain", str(manifest))
                self.assertEqual(explained["manifest"]["id"], "skill-forward")
                before = self.snapshot(platform)
                self.invoke(platform, "--dry-run", "update", str(manifest))
                self.assertEqual(self.snapshot(platform), before)
                self.invoke(platform, "update", str(manifest))
                self.assertEqual(self.invoke(platform, "show", "skill-forward")["service"]["manifest"]["args"], ["updated"])
                before = self.snapshot(platform)
                self.invoke(platform, "--dry-run", "remove", "skill-forward")
                self.assertEqual(self.snapshot(platform), before)
                self.invoke(platform, "remove", "skill-forward")
                self.assertEqual(self.invoke(platform, "list")["services"], [])

    def test_runtime_plans_never_execute_managers_offline(self) -> None:
        for platform in ("linux", "macos"):
            with self.subTest(platform=platform):
                self.invoke(platform, *self.add_args())
                before = self.snapshot(platform)
                for action in ("start", "stop", "restart", "enable", "disable"):
                    plan = self.invoke(platform, "--dry-run", action, "skill-forward")
                    self.assertTrue(plan["dry_run"])
                    self.assertEqual(plan["action"], action)
                    self.assertEqual(self.invoke(platform, action, "skill-forward", ok=False)["code"], "offline_only")
                self.assertEqual(self.invoke(platform, "status", "skill-forward", ok=False)["code"], "offline_only")
                self.assertEqual(self.invoke(platform, "logs", "skill-forward", ok=False)["code"], "unsupported_capability")
                doctor = self.invoke(platform, "doctor")
                self.assertTrue(doctor["state"]["ok"])
                self.assertFalse(doctor["session"]["checked"])
                self.assertEqual(self.snapshot(platform), before)

    def test_discovery_does_not_adopt_foreign_files_and_doctor_checks_nested_health(self) -> None:
        for platform in ("linux", "macos"):
            with self.subTest(platform=platform):
                self.invoke(platform, *self.add_args())
                native = self.work / platform / "native"
                foreign = native / ("foreign.service" if platform == "linux" else "foreign.plist")
                foreign.write_text("foreign bytes remain untouched\n")
                before = self.snapshot(platform)
                entries = self.invoke(platform, "discover")["definitions"]
                entry = next(item for item in entries if item["name"] == foreign.name)
                self.assertFalse(entry["managed"])
                self.assertTrue(entry["read_only"])
                self.assertEqual(self.snapshot(platform), before)
                journal = self.work / platform / "state/.pending.json"
                journal.write_text("{}\n")
                doctor = self.invoke(platform, "doctor")
                self.assertFalse(doctor["state"]["ok"])
                self.assertEqual(doctor["state"]["code"], "recovery_required")
                self.assertTrue(journal.exists())


if __name__ == "__main__":
    unittest.main()
