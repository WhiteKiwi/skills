from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NODE = shutil.which("node")


@unittest.skipUnless(NODE, "Node.js is not installed")
class ContrastCheckerTests(unittest.TestCase):
    script = ROOT / "skills/design-guidelines/scripts/contrast-check.mjs"

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [NODE, str(self.script), *args],
            text=True, capture_output=True, check=False, timeout=10,
        )

    def test_shorthand_and_reversed_pairs_have_the_same_known_ratio(self) -> None:
        result = self.invoke("--json", "#000:#fff", "fff:000")
        self.assertEqual(result.returncode, 0)
        data = json.loads(result.stdout)
        self.assertEqual(data["errors"], [])
        self.assertEqual([pair["ratio"] for pair in data["results"]], [21, 21])
        self.assertEqual(data["results"][0]["foreground"], "#000000")
        self.assertTrue(data["results"][0]["aaaText"])

    def test_report_mode_and_gate_have_different_failure_behavior(self) -> None:
        report = self.invoke("--json", "#fff:#fff")
        self.assertEqual(report.returncode, 0)
        self.assertEqual(json.loads(report.stdout)["results"][0]["ratio"], 1)
        gate = self.invoke("--min", "4.5", "--json", "#fff:#fff")
        self.assertEqual(gate.returncode, 1)
        self.assertFalse(json.loads(gate.stdout)["results"][0]["meetsMinimum"])

    def test_gate_uses_the_selected_role_threshold(self) -> None:
        ordinary = self.invoke("--min=4.5", "--json", "#777:#fff")
        large = self.invoke("--min=3", "--json", "#777:#fff")
        self.assertEqual(ordinary.returncode, 1)
        self.assertEqual(large.returncode, 0)
        pair = json.loads(large.stdout)["results"][0]
        self.assertFalse(pair["aaText"])
        self.assertTrue(pair["largeTextAndUI"])

    def test_gate_does_not_round_a_near_threshold_failure_into_a_pass(self) -> None:
        result = self.invoke("--min", "3", "--json", "#959595:#ffffff")
        self.assertEqual(result.returncode, 1)
        pair = json.loads(result.stdout)["results"][0]
        self.assertLess(pair["ratio"], 3)
        self.assertEqual(round(pair["ratio"], 2), 3)
        self.assertFalse(pair["largeTextAndUI"])

    def test_one_failed_pair_fails_the_gate_and_keeps_all_results(self) -> None:
        result = self.invoke("--json", "--min", "4.5", "#000:#fff", "#fff:#C6FF4A")
        self.assertEqual(result.returncode, 1)
        pairs = json.loads(result.stdout)["results"]
        self.assertEqual([pair["meetsMinimum"] for pair in pairs], [True, False])

    def test_invalid_input_is_distinct_from_a_missed_threshold(self) -> None:
        cases = [
            ("#abcd:#fff",), ("#ffffff80:#000",), ("#fff",),
            ("#fff:#000:extra",), ("--min", "nan", "#000:#fff"),
            ("--min", "0", "#000:#fff"), ("--min", "22", "#000:#fff"),
            ("--min", "4.5", "--min", "3", "#000:#fff"),
            ("--unknown", "#000:#fff"), ("--min",), (),
        ]
        for args in cases:
            with self.subTest(args=args):
                result = self.invoke("--json", *args)
                self.assertEqual(result.returncode, 2)
                self.assertTrue(json.loads(result.stdout)["errors"])

    def test_human_output_and_help_explain_the_gate(self) -> None:
        result = self.invoke("--min", "3", "#959595:#fff")
        self.assertEqual(result.returncode, 1)
        self.assertIn("minimum 3: fail", result.stdout)
        help_result = self.invoke("--help")
        self.assertEqual(help_result.returncode, 0)
        self.assertIn("1 missed threshold", help_result.stdout)

    def test_missing_minimum_does_not_consume_the_json_option(self) -> None:
        result = self.invoke("--min", "--json", "#000:#fff")
        self.assertEqual(result.returncode, 2)
        self.assertTrue(json.loads(result.stdout)["errors"])


class CreateDesignGuidelineContrastTests(ContrastCheckerTests):
    script = ROOT / "skills/create-design-guideline/scripts/contrast-check.mjs"


if __name__ == "__main__":
    unittest.main()
