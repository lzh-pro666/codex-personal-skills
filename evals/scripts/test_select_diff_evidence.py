#!/usr/bin/env python3
"""Behavior tests for bounded PR diff selection."""

from __future__ import annotations

import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/pr-review-to-notion/scripts/select_diff_evidence.py"


DIFF = """diff --git a/Sources/A.swift b/Sources/A.swift
index 1111111..2222222 100644
--- a/Sources/A.swift
+++ b/Sources/A.swift
@@ -1,2 +1,3 @@
-let value = 1
+let value = 2
+let added = true
diff --git a/Web/feature.ts b/Web/feature.ts
index 3333333..4444444 100644
--- a/Web/feature.ts
+++ b/Web/feature.ts
@@ -1,2 +1,5 @@
-export const value = 1
+export const value = 2
+export const one = 1
+export const two = 2
+export const three = 3
+export const four = 4
"""


class SelectDiffEvidenceTests(unittest.TestCase):
    def run_selector(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            evidence = pathlib.Path(directory)
            (evidence / "pr.diff").write_text(DIFF, encoding="utf-8")
            return subprocess.run(
                ["python3", str(SCRIPT), str(evidence), *arguments],
                capture_output=True,
                text=True,
            )

    def test_selects_only_requested_file(self) -> None:
        result = self.run_selector("--path", "Web/feature.ts")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["files"], ["Web/feature.ts"])
        self.assertNotIn("Sources/A.swift", payload["diff"])
        self.assertIn("export const value = 2", payload["diff"])

    def test_truncates_at_explicit_line_limit(self) -> None:
        result = self.run_selector("--path", "Web/feature.ts", "--max-lines", "6")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["truncated"])
        self.assertEqual(payload["returned_lines"], 6)
        self.assertGreater(payload["original_lines"], payload["returned_lines"])

    def test_requires_a_path_selector(self) -> None:
        result = self.run_selector()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("provide at least one --path", result.stderr)


if __name__ == "__main__":
    unittest.main()
