#!/usr/bin/env python3
"""Behavior tests for immutable generative-evaluation evidence."""

from __future__ import annotations

import json
import pathlib
import shutil
import tempfile
import unittest

from run_generative_eval import (
    EXPECTED_BASELINE_DIAGNOSTICS,
    EXPECTED_REDUCER_RED_TEST_NAME,
    SNAPSHOT_SCHEMA_VERSION,
    create_input_manifest,
    prepare_reducer_red_harness,
    sha256_record,
    validate_immutable_inputs,
    validate_independent_graders,
    validate_verification_snapshot,
)


class GenerativeVerificationTests(unittest.TestCase):
    def make_input_run(self) -> tuple[pathlib.Path, pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name).resolve()
        baseline = root / "baseline"
        run = root / "run"
        for package in (baseline, run / "code-drills"):
            (package / "Sources/CodeQualityDrills").mkdir(parents=True)
            (package / "Tests/CodeQualityDrillsTests").mkdir(parents=True)
            (package / "Package.swift").write_text("// package\n", encoding="utf-8")
            (package / "Sources/CodeQualityDrills/Drills.swift").write_text(
                "let value = 1\n", encoding="utf-8"
            )
            tests = "\n".join(f'@Test("test-{index}")' for index in range(20)) + "\n"
            (package / "Tests/CodeQualityDrillsTests/DrillsTests.swift").write_text(
                tests, encoding="utf-8"
            )
        (run / "blind-packets.jsonl").write_text(
            json.dumps({"id": "case-1", "artifact_type": "code"}) + "\n",
            encoding="utf-8",
        )
        (run / "artifacts").mkdir()
        (run / "artifacts/case-1.md").write_text(
            "```mermaid\nflowchart LR\nA --> B\n```\n",
            encoding="utf-8",
        )
        prepare_reducer_red_harness(run, baseline)
        create_input_manifest(run, baseline, "test-run")
        return run, baseline

    def make_verified_run(self) -> tuple[pathlib.Path, pathlib.Path]:
        run, baseline = self.make_input_run()
        logs = {
            "baseline-red.log": (
                f"command: swift test --package-path {baseline}\n"
                "exit_code: 1\n"
                + "\n".join(EXPECTED_BASELINE_DIAGNOSTICS)
                + "\n"
            ),
            "reducer-red.log": (
                f"command: swift test --package-path {run / 'reducer-red'}\n"
                "exit_code: 1\n"
                f'Test "{EXPECTED_REDUCER_RED_TEST_NAME}" recorded an issue\n'
                'Expectation failed: (state.messages → ["stale"]).isEmpty\n'
                "Test run with 1 test in 1 suite failed\n"
            ),
            "swift-test.log": (
                f"command: swift test --package-path {run / 'code-drills'}\n"
                "exit_code: 0\n"
                "Test run with 20 tests in 0 suites passed\n"
            ),
            "ios-typecheck.log": (
                f"command: xcrun swiftc -typecheck {run / 'code-drills/Sources/CodeQualityDrills/Drills.swift'}\n"
                "exit_code: 0\n"
            ),
        }
        for name, content in logs.items():
            (run / name).write_text(content, encoding="utf-8")
        (run / "mermaid-render").mkdir()
        (run / "mermaid-render/case-1-1.svg").write_text("<svg/>\n", encoding="utf-8")

        manifest = json.loads((run / "input-manifest.json").read_text(encoding="utf-8"))
        snapshot = {
            "schema_version": SNAPSHOT_SCHEMA_VERSION,
            "run_id": "test-run",
            "inputs": {
                "manifest": sha256_record(run / "input-manifest.json", run),
                "files": manifest["run_inputs"],
            },
            "artifacts": [sha256_record(run / "artifacts/case-1.md", run)],
            "baseline": {
                "command": ["swift", "test", "--package-path", str(baseline)],
                "exit_code": 1,
                "expected_diagnostics": list(EXPECTED_BASELINE_DIAGNOSTICS),
                "log": sha256_record(run / "baseline-red.log", run),
            },
            "reducer_red": {
                "command": ["swift", "test", "--package-path", str(run / "reducer-red")],
                "exit_code": 1,
                "expected_test_name": EXPECTED_REDUCER_RED_TEST_NAME,
                "expected_test_count": 1,
                "source": sha256_record(
                    run / "reducer-red/Sources/CodeQualityDrills/Drills.swift", run
                ),
                "log": sha256_record(run / "reducer-red.log", run),
            },
            "swift_test": {
                "command": ["swift", "test", "--package-path", str(run / "code-drills")],
                "exit_code": 0,
                "expected_test_count": 20,
                "log": sha256_record(run / "swift-test.log", run),
            },
            "ios_typecheck": {
                "command": [
                    "xcrun", "swiftc", "-typecheck",
                    str(run / "code-drills/Sources/CodeQualityDrills/Drills.swift"),
                ],
                "exit_code": 0,
                "log": sha256_record(run / "ios-typecheck.log", run),
            },
            "mermaid": {
                "requested": True,
                "source_blocks": 1,
                "rendered_count": 1,
                "outputs": [sha256_record(run / "mermaid-render/case-1-1.svg", run)],
            },
        }
        (run / "verification.json").write_text(json.dumps(snapshot), encoding="utf-8")
        return run, baseline

    def write_grader(self, path: pathlib.Path, grader_id: str) -> None:
        row = {
            "grader_id": grader_id,
            "case_id": "case-1",
            "score": 95,
            "decision": "pass",
            "evidence": ["artifact evidence"],
            "issues": [],
        }
        path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    def test_accepts_complete_verified_snapshot(self) -> None:
        run, baseline = self.make_verified_run()
        validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_tampered_test_input(self) -> None:
        run, baseline = self.make_input_run()
        test_path = run / "code-drills/Tests/CodeQualityDrillsTests/DrillsTests.swift"
        test_path.write_text("// weakened tests\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            validate_immutable_inputs(run, baseline, "test-run")

    def test_rejects_tampered_package_manifest(self) -> None:
        run, baseline = self.make_input_run()
        (run / "code-drills/Package.swift").write_text("// replaced package\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            validate_immutable_inputs(run, baseline, "test-run")

    def test_rejects_tampered_baseline_fixture(self) -> None:
        run, baseline = self.make_input_run()
        (baseline / "Sources/CodeQualityDrills/Drills.swift").write_text(
            "let weakenedBaseline = true\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            validate_immutable_inputs(run, baseline, "test-run")

    def test_rejects_forged_snapshot_hash(self) -> None:
        run, baseline = self.make_verified_run()
        (run / "swift-test.log").write_text("forged green evidence\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "SHA256 mismatch"):
            validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_rehashed_forged_reducer_red_log(self) -> None:
        run, baseline = self.make_verified_run()
        log = run / "reducer-red.log"
        log.write_text(
            f"command: swift test --package-path {run / 'reducer-red'}\n"
            "exit_code: 1\n"
            "Test run with 1 test in 1 suite failed\n",
            encoding="utf-8",
        )
        snapshot = json.loads((run / "verification.json").read_text(encoding="utf-8"))
        snapshot["reducer_red"]["log"] = sha256_record(log, run)
        (run / "verification.json").write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "focused reducer RED evidence"):
            validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_rehashed_reducer_source_not_matching_baseline(self) -> None:
        run, baseline = self.make_verified_run()
        source = run / "reducer-red/Sources/CodeQualityDrills/Drills.swift"
        source.write_text("let forgedReducer = true\n", encoding="utf-8")
        manifest_path = run / "input-manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for record in manifest["run_inputs"]:
            if record["path"] == "reducer-red/Sources/CodeQualityDrills/Drills.swift":
                record.update(sha256_record(source, run))
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        snapshot_path = run / "verification.json"
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        snapshot["inputs"]["manifest"] = sha256_record(manifest_path, run)
        snapshot["inputs"]["files"] = manifest["run_inputs"]
        snapshot["reducer_red"]["source"] = sha256_record(source, run)
        snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "focused reducer source"):
            validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_snapshot_with_path_traversal(self) -> None:
        run, baseline = self.make_verified_run()
        snapshot = json.loads((run / "verification.json").read_text(encoding="utf-8"))
        snapshot["swift_test"]["log"]["path"] = "../outside.log"
        (run / "verification.json").write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "safe relative path"):
            validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_snapshot_with_extra_schema_key(self) -> None:
        run, baseline = self.make_verified_run()
        snapshot = json.loads((run / "verification.json").read_text(encoding="utf-8"))
        snapshot["untrusted"] = True
        (run / "verification.json").write_text(json.dumps(snapshot), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "invalid schema"):
            validate_verification_snapshot(run, expected_run_id="test-run", baseline_package=baseline)

    def test_rejects_same_grader_file_twice(self) -> None:
        run, _ = self.make_input_run()
        grader = run / "grader.jsonl"
        self.write_grader(grader, "grader-a")

        with self.assertRaisesRegex(ValueError, "different files"):
            validate_independent_graders([grader, grader], {"case-1"})

    def test_rejects_same_grader_id_in_different_files(self) -> None:
        run, _ = self.make_input_run()
        left = run / "left.jsonl"
        right = run / "right.jsonl"
        self.write_grader(left, "grader-a")
        shutil.copyfile(left, right)

        with self.assertRaisesRegex(ValueError, "distinct grader_id"):
            validate_independent_graders([left, right], {"case-1"})


if __name__ == "__main__":
    unittest.main()
