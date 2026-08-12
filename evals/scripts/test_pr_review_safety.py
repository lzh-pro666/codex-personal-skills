#!/usr/bin/env python3
"""Behavior tests for bounded PR-review context and Notion write safety."""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
BUILD_INDEX = ROOT / "skills/pr-review-to-notion/scripts/build_evidence_index.py"
SELECT_REVIEW = ROOT / "skills/pr-review-to-notion/scripts/select_review_evidence.py"
VALIDATE_DRAFT = ROOT / "skills/pr-review-to-notion/scripts/validate_draft.py"
PR_URL = "https://github.com/example/project/pull/42"
REQUIRED_HEADINGS = (
    "证据与数据缺口",
    "PR 类型与一句话结论",
    "这个 PR 改变了什么",
    "关键实现与取舍",
    "改造前后对比",
    "风险、遗漏与建议",
    "我能学到什么",
)


def write_json(path: pathlib.Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReviewDigestTests(unittest.TestCase):
    def make_bundle(self, evidence: pathlib.Path) -> None:
        write_json(
            evidence / "pr.json",
            {
                "html_url": PR_URL,
                "title": "Bound review evidence",
                "user": {"login": "author"},
                "base": {
                    "ref": "main",
                    "sha": "a" * 40,
                    "repo": {"full_name": "example/project"},
                },
                "head": {"ref": "feature", "sha": "b" * 40},
            },
        )
        (evidence / "pr.diff").write_text(
            "diff --git a/Sources/App.swift b/Sources/App.swift\n"
            "--- a/Sources/App.swift\n+++ b/Sources/App.swift\n@@ -1 +1 @@\n-old\n+new\n",
            encoding="utf-8",
        )
        write_json(
            evidence / "files.json",
            [{"filename": "Sources/App.swift", "status": "modified", "changes": 2}],
        )
        write_json(evidence / "commits.json", [])
        write_json(
            evidence / "reviews.json",
            [
                {
                    "id": 1000 + index,
                    "user": {"login": f"reviewer-{index}", "type": "User"},
                    "body": f"review-{index} " + ("detail " * 60),
                }
                for index in range(12)
            ],
        )
        write_json(
            evidence / "review_comments.json",
            [
                {
                    "id": 2000 + index,
                    "user": {"login": f"commenter-{index}", "type": "User"},
                    "path": f"Sources/File{index}.swift",
                    "body": f"inline-{index} " + ("full targeted detail " * 12),
                }
                for index in range(11)
            ],
        )
        write_json(
            evidence / "issue_comments.json",
            [
                {
                    "id": 3000 + index,
                    "user": {"login": f"participant-{index}", "type": "User"},
                    "body": f"issue-{index} " + ("context " * 40),
                }
                for index in range(10)
            ],
        )

    def test_digest_is_bounded_and_full_body_requires_targeted_selector(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            evidence = pathlib.Path(directory)
            self.make_bundle(evidence)

            built = subprocess.run(
                ["python3", str(BUILD_INDEX), str(evidence), "--history-mode", "none"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(built.returncode, 0, built.stderr)
            digest = json.loads((evidence / "review_digest.json").read_text(encoding="utf-8"))

            self.assertEqual(
                digest["counts"],
                {"reviews": 12, "review_comments": 11, "issue_comments": 10},
            )
            self.assertEqual(digest["sample_limit_per_kind"], 8)
            self.assertEqual(
                set(digest["samples"]),
                {"reviews", "review_comments", "issue_comments"},
            )
            for entries in digest["samples"].values():
                self.assertLessEqual(len(entries), 8)
                for entry in entries:
                    self.assertEqual(set(entry), {"id", "path", "user", "summary"})
                    self.assertLessEqual(len(entry["summary"]), 160)
            self.assertNotIn('"body"', json.dumps(digest, ensure_ascii=False))
            self.assertNotIn("inline-10", json.dumps(digest, ensure_ascii=False))

            selected = subprocess.run(
                [
                    "python3",
                    str(SELECT_REVIEW),
                    str(evidence),
                    "--kind",
                    "review-comments",
                    "--id",
                    "2010",
                    "--body-limit",
                    "1000",
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(selected.returncode, 0, selected.stderr)
            selected_payload = json.loads(selected.stdout)
            self.assertEqual(selected_payload["count"], 1)
            self.assertIn("inline-10", selected_payload["results"][0]["body"])
            self.assertFalse(selected_payload["results"][0]["body_truncated"])


class DraftSensitiveContentTests(unittest.TestCase):
    def run_validator(
        self,
        *,
        body_suffix: str = "",
        property_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as directory:
            evidence = pathlib.Path(directory)
            source = evidence / "pr.diff"
            source.write_text("diff evidence\n", encoding="utf-8")
            write_json(
                evidence / "evidence_manifest.json",
                {"files": {"pr.diff": {"bytes": source.stat().st_size, "sha256": sha256(source)}}},
            )
            write_json(
                evidence / "evidence_summary.json",
                {"pr_url": PR_URL, "title": "Raw PR title"},
            )
            body = [PR_URL]
            for index, heading in enumerate(REQUIRED_HEADINGS):
                body.extend((f"## {heading}", "有界事实。"))
                if index == 0 and body_suffix:
                    body.append(body_suffix)
            (evidence / "retrospective.md").write_text("\n\n".join(body) + "\n", encoding="utf-8")
            properties = {
                "标题": "收紧 PR 证据归档边界",
                "PR 链接": PR_URL,
                "原PR标题": "Raw PR title",
                "总结": "改进写入安全。",
                "学习": "在外部写入前验证。",
                "优化": "使用有界证据。",
            }
            properties.update(property_overrides or {})
            write_json(evidence / "notion-properties.json", properties)
            return subprocess.run(
                ["python3", str(VALIDATE_DRAFT), str(evidence)],
                capture_output=True,
                text=True,
            )

    def test_blocks_secret_in_retrospective_without_echoing_value(self) -> None:
        credential = "not-a-real-" + "credential-value-123456"
        authorization = "Authorization: " + "Bear" + "er " + credential
        result = self.run_validator(body_suffix=authorization)
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("possible secret", output)
        self.assertIn("[REDACTED_SECRET]", output)
        self.assertNotIn(credential, output)

    def test_blocks_obvious_pii_in_notion_properties_without_echoing_values(self) -> None:
        email = "person" + "@" + "example.com"
        phone = "138" + "00138000"
        result = self.run_validator(property_overrides={"总结": f"联系 {email} 或 {phone}"})
        output = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("possible email address", output)
        self.assertIn("possible phone number", output)
        self.assertIn("[REDACTED_EMAIL]", output)
        self.assertIn("[REDACTED_PHONE]", output)
        self.assertNotIn(email, output)
        self.assertNotIn(phone, output)

    def test_allows_unlabelled_git_and_content_hashes(self) -> None:
        body = f"head commit {'a' * 40}; artifact checksum {'b' * 64}"
        result = self.run_validator(body_suffix=body)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
