#!/usr/bin/env python3
"""Tests for live real-project evidence and source-integrity checks."""

from __future__ import annotations

import hashlib
import pathlib
import subprocess
import tempfile
import unittest

from validate_real_project_report import (
    changed_files,
    evidence_file,
    repository_fingerprint,
    validate_live_state,
)


class RealProjectLiveValidationTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory, pathlib.Path]:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "Eval"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "eval@example.invalid"], check=True)
        (root / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-qm", "base"], check=True)
        return temporary, root

    def test_fingerprint_changes_when_already_modified_content_changes(self) -> None:
        _, root = self.make_repo()
        target = root / "tracked.txt"
        target.write_text("first dirty value\n", encoding="utf-8")
        before = repository_fingerprint(root)
        target.write_text("second dirty value\n", encoding="utf-8")

        self.assertNotEqual(before, repository_fingerprint(root))

    def test_changed_files_includes_staged_and_untracked_paths(self) -> None:
        _, root = self.make_repo()
        (root / "tracked.txt").write_text("staged\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "tracked.txt"], check=True)
        (root / "untracked.txt").write_text("new\n", encoding="utf-8")

        self.assertEqual(changed_files(root), {"tracked.txt", "untracked.txt"})

    def test_evidence_record_rejects_content_hash_mismatch(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        log = root / "command.log"
        log.write_text("command: test\nexit_code: 0\npassed\n", encoding="utf-8")
        record = {"path": "command.log", "sha256": hashlib.sha256(log.read_bytes()).hexdigest()}
        self.assertEqual(evidence_file(root, record), log.resolve())
        log.write_text("command: test\nexit_code: 0\nforged\n", encoding="utf-8")
        self.assertIsNone(evidence_file(root, record))

    def test_live_state_rejects_source_head_newer_than_evaluation_base(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        container = pathlib.Path(temporary.name)
        source = container / "source"
        subprocess.run(["git", "init", "-q", str(source)], check=True)
        subprocess.run(["git", "-C", str(source), "config", "user.name", "Eval"], check=True)
        subprocess.run(["git", "-C", str(source), "config", "user.email", "eval@example.invalid"], check=True)
        (source / "tracked.txt").write_text("base\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(source), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(source), "commit", "-qm", "base"], check=True)
        base = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        worktree = container / "evaluation"
        subprocess.run(
            ["git", "-C", str(source), "worktree", "add", "-qb", "codex/eval", str(worktree), base],
            check=True,
        )
        (source / "tracked.txt").write_text("new source HEAD\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(source), "add", "tracked.txt"], check=True)
        subprocess.run(["git", "-C", str(source), "commit", "-qm", "advance"], check=True)
        fingerprint = repository_fingerprint(source)
        report = {
            "case_id": "head-mismatch",
            "source_status_before": fingerprint,
            "source_status_after": fingerprint,
            "branch": "codex/eval",
            "base_commit": base,
            "changed_files": [],
        }

        errors = validate_live_state(report, source, worktree)

        self.assertTrue(any("source HEAD" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
