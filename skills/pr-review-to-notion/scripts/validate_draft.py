#!/usr/bin/env python3
"""Validate a PR retrospective draft before any external write."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re


PROPERTY_KEYS = {"标题", "PR 链接", "原PR标题", "总结", "学习", "优化"}
RICH_TEXT_KEYS = {"原PR标题", "总结", "学习", "优化"}
REQUIRED_HEADINGS = (
    "证据与数据缺口",
    "PR 类型与一句话结论",
    "这个 PR 改变了什么",
    "关键实现与取舍",
    "改造前后对比",
    "风险、遗漏与建议",
    "我能学到什么",
)
SENSITIVE_PATTERNS = (
    (
        "possible secret (private key)",
        "[REDACTED_SECRET]",
        re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----", re.IGNORECASE),
    ),
    (
        "possible secret (known credential prefix)",
        "[REDACTED_SECRET]",
        re.compile(
            r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|"
            r"sk-[A-Za-z0-9_-]{20,}|xox[baprs]-[A-Za-z0-9-]{12,}|AKIA[0-9A-Z]{16})\b"
        ),
    ),
    (
        "possible secret (authorization value)",
        "[REDACTED_SECRET]",
        re.compile(
            r"\bauthorization\s*:\s*(?:bearer|basic)\s+"
            r"(?!\[REDACTED_SECRET\])\S{12,}",
            re.IGNORECASE,
        ),
    ),
    (
        "possible secret (credential-labelled value)",
        "[REDACTED_SECRET]",
        re.compile(
            r"\b(?:api[_ -]?key|access[_ -]?token|auth[_ -]?token|"
            r"client[_ -]?secret|password|passwd|secret)\s*[:=]\s*"
            r"(?!\[REDACTED_SECRET\])[\"']?[A-Za-z0-9._~+/=-]{12,}",
            re.IGNORECASE,
        ),
    ),
    (
        "possible email address",
        "[REDACTED_EMAIL]",
        re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    ),
    (
        "possible phone number",
        "[REDACTED_PHONE]",
        re.compile(
            r"(?<![A-Z0-9+])(?:\+[1-9][0-9]{8,14}|1[3-9][0-9]{9})(?![0-9])",
            re.IGNORECASE,
        ),
    ),
)


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sensitive_findings(text: str, location: str) -> list[str]:
    findings = []
    seen = set()
    for label, placeholder, pattern in SENSITIVE_PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            finding = (
                f"{location}:{line}: {label}; replace the value with {placeholder} "
                "before any Notion write"
            )
            if finding not in seen:
                seen.add(finding)
                findings.append(finding)
    return findings


def validate_sensitive_content(evidence_dir: pathlib.Path, errors: list[str]) -> None:
    retrospective = evidence_dir / "retrospective.md"
    try:
        errors.extend(sensitive_findings(retrospective.read_text(encoding="utf-8"), retrospective.name))
    except OSError:
        pass  # The structural validator reports the missing or unreadable file.

    properties_path = evidence_dir / "notion-properties.json"
    try:
        properties = read_json(properties_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return  # The property validator reports malformed JSON.
    if not isinstance(properties, dict):
        return
    for key, value in properties.items():
        if isinstance(value, str):
            errors.extend(sensitive_findings(value, f"{properties_path.name} property {key}"))


def validate_manifest(evidence_dir: pathlib.Path, errors: list[str]) -> None:
    path = evidence_dir / "evidence_manifest.json"
    try:
        manifest = read_json(path).get("files", {})
    except (OSError, ValueError, json.JSONDecodeError, AttributeError) as error:
        errors.append(f"invalid evidence_manifest.json: {error}")
        return
    if not isinstance(manifest, dict) or not manifest:
        errors.append("evidence_manifest.json has no files")
        return
    for name, expected in manifest.items():
        source = evidence_dir / name
        if not source.is_file():
            errors.append(f"manifest file is missing: {name}")
            continue
        if source.stat().st_size != expected.get("bytes"):
            errors.append(f"manifest byte count mismatch: {name}")
        if sha256(source) != expected.get("sha256"):
            errors.append(f"manifest SHA256 mismatch: {name}")


def validate_properties(evidence_dir: pathlib.Path, summary: dict, errors: list[str]) -> None:
    path = evidence_dir / "notion-properties.json"
    try:
        properties = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        errors.append(f"invalid notion-properties.json: {error}")
        return
    if not isinstance(properties, dict):
        errors.append("notion-properties.json must be an object")
        return
    actual = set(properties)
    if actual != PROPERTY_KEYS:
        errors.append(
            "notion property keys must be exactly: " + ", ".join(sorted(PROPERTY_KEYS))
        )
        return
    invalid_value = False
    for key in PROPERTY_KEYS & actual:
        value = properties[key]
        if not isinstance(value, str) or not value.strip():
            errors.append(f"property must be a non-empty string: {key}")
            invalid_value = True
    if invalid_value:
        return
    if properties["PR 链接"].strip() != str(summary.get("pr_url") or "").strip():
        errors.append("PR 链接 does not match evidence_summary.json")
    if properties["原PR标题"] != summary.get("title"):
        errors.append("原PR标题 does not exactly match evidence_summary.json")
    if properties["标题"].strip() == properties["原PR标题"].strip():
        errors.append("标题 must be a Chinese result-oriented title, not the raw PR title")
    for key in RICH_TEXT_KEYS:
        if len(properties[key]) >= 1800:
            errors.append(f"property must be below 1800 characters: {key}")


def validate_retrospective(evidence_dir: pathlib.Path, summary: dict, errors: list[str]) -> None:
    path = evidence_dir / "retrospective.md"
    try:
        body = path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"invalid retrospective.md: {error}")
        return
    if not body.strip():
        errors.append("retrospective.md is empty")
        return
    pr_url = str(summary.get("pr_url") or "")
    if pr_url and pr_url not in body:
        errors.append("retrospective.md does not contain the canonical PR URL")
    positions = []
    for heading in REQUIRED_HEADINGS:
        matches = list(re.finditer(rf"(?m)^## {re.escape(heading)}\s*$", body))
        if len(matches) != 1:
            errors.append(f"required heading must appear exactly once: {heading}")
        else:
            positions.append(matches[0].start())
    if len(positions) == len(REQUIRED_HEADINGS) and positions != sorted(positions):
        errors.append("required retrospective headings are out of order")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=pathlib.Path)
    args = parser.parse_args()
    evidence_dir = args.evidence_dir.resolve()
    errors: list[str] = []

    try:
        summary = read_json(evidence_dir / "evidence_summary.json")
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"error: invalid evidence_summary.json: {error}") from error
    if not isinstance(summary, dict) or not summary.get("pr_url") or not summary.get("title"):
        raise SystemExit("error: evidence_summary.json is missing PR identity")

    validate_manifest(evidence_dir, errors)
    validate_properties(evidence_dir, summary, errors)
    validate_retrospective(evidence_dir, summary, errors)
    validate_sensitive_content(evidence_dir, errors)

    if errors:
        for error in errors:
            print(f"error: {error}")
        raise SystemExit(1)
    print(
        json.dumps(
            {
                "valid": True,
                "pr_url": summary["pr_url"],
                "retrospective": str(evidence_dir / "retrospective.md"),
                "properties": str(evidence_dir / "notion-properties.json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
