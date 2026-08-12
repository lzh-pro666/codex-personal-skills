#!/usr/bin/env python3
"""Validate evidence reports produced by isolated real-project evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

from validate_scorecard import validate as validate_scorecard


ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES = ROOT / "evals/cases/real-project-cases.jsonl"


def load_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def nonempty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def evidence_file(root: pathlib.Path, record: object) -> pathlib.Path | None:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        return None
    relative = record.get("path")
    expected = record.get("sha256")
    if not isinstance(relative, str) or not relative or not re.fullmatch(r"[0-9a-f]{64}", str(expected)):
        return None
    pure = pathlib.PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        return None
    target = (root / pathlib.Path(*pure.parts)).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return None
    if not target.is_file() or target.is_symlink() or sha256_file(target) != expected:
        return None
    return target


def validate_command(
    value: object, *, expect_success: bool, evidence_root: pathlib.Path | None = None,
) -> bool:
    expected_keys = {"command", "exit_code", "evidence"}
    if evidence_root is not None:
        expected_keys.add("log")
    if not isinstance(value, dict) or set(value) != expected_keys:
        return False
    exit_code = value.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        return False
    if expect_success and exit_code != 0:
        return False
    if not expect_success and exit_code == 0:
        return False
    command = value.get("command")
    if not isinstance(command, str) or not command.strip() or not nonempty_strings(value.get("evidence")):
        return False
    if evidence_root is not None:
        log = evidence_file(evidence_root, value.get("log"))
        if log is None:
            return False
        try:
            header = log.read_text(encoding="utf-8").splitlines()[:2]
        except (OSError, UnicodeDecodeError):
            return False
        if header != [f"command: {command}", f"exit_code: {exit_code}"]:
            return False
    return True


def git(path: pathlib.Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args], capture_output=True, text=True,
    )


def git_bytes(path: pathlib.Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(path), *args], capture_output=True)


def repository_fingerprint(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    for args in (
        ("rev-parse", "HEAD"),
        ("diff", "--binary"),
        ("diff", "--cached", "--binary"),
    ):
        result = git_bytes(path, *args)
        if result.returncode:
            raise ValueError(result.stderr.decode(errors="replace").strip() or f"cannot inspect {path}")
        digest.update(" ".join(args).encode("utf-8") + b"\0" + result.stdout)
    untracked = git_bytes(path, "ls-files", "--others", "--exclude-standard", "-z")
    if untracked.returncode:
        raise ValueError(untracked.stderr.decode(errors="replace").strip())
    for raw_relative in sorted(item for item in untracked.stdout.split(b"\0") if item):
        relative = raw_relative.decode("utf-8", errors="surrogateescape")
        target = path / relative
        if target.is_symlink():
            digest.update(b"untracked-symlink\0" + raw_relative + b"\0")
            digest.update(str(target.readlink()).encode("utf-8", errors="surrogateescape"))
            continue
        if target.is_dir():
            digest.update(b"untracked-directory\0" + raw_relative + b"\0")
            for child in sorted(target.rglob("*")):
                child_relative = child.relative_to(target)
                if ".git" in child_relative.parts:
                    continue
                encoded = child_relative.as_posix().encode("utf-8", errors="surrogateescape")
                if child.is_symlink():
                    digest.update(b"symlink\0" + encoded + b"\0")
                    digest.update(str(child.readlink()).encode("utf-8", errors="surrogateescape"))
                elif child.is_file():
                    digest.update(b"file\0" + encoded + b"\0")
                    with child.open("rb") as handle:
                        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                            digest.update(chunk)
            continue
        if not target.is_file():
            raise ValueError(f"unsupported untracked entry: {relative}")
        digest.update(b"untracked\0" + raw_relative + b"\0")
        with target.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return digest.hexdigest()


def changed_files(path: pathlib.Path) -> set[str]:
    tracked = git(path, "diff", "--name-only", "HEAD")
    untracked = git(path, "ls-files", "--others", "--exclude-standard")
    if tracked.returncode or untracked.returncode:
        raise ValueError((tracked.stderr + untracked.stderr).strip())
    return {line for line in (tracked.stdout + untracked.stdout).splitlines() if line}


def validate_live_state(
    report: dict, source: pathlib.Path, worktree: pathlib.Path,
) -> list[str]:
    case_id = report["case_id"]
    errors: list[str] = []
    if not source.is_dir() or not worktree.is_dir():
        return [f"{case_id}: live source or evaluation worktree is missing"]
    try:
        current_source = repository_fingerprint(source)
        current_files = changed_files(worktree)
    except ValueError as error:
        return [f"{case_id}: live Git inspection failed: {error}"]
    if current_source != report["source_status_before"] or current_source != report["source_status_after"]:
        errors.append(f"{case_id}: live source fingerprint does not match the report")
    branch = git(worktree, "branch", "--show-current")
    head = git(worktree, "rev-parse", "HEAD")
    source_head = git(source, "rev-parse", "HEAD")
    if source_head.returncode or source_head.stdout.strip() != report["base_commit"]:
        errors.append(f"{case_id}: source HEAD does not match the evaluation base commit")
    if branch.returncode or branch.stdout.strip() != report["branch"]:
        errors.append(f"{case_id}: live evaluation branch mismatch")
    if head.returncode or head.stdout.strip() != report["base_commit"]:
        errors.append(f"{case_id}: live evaluation HEAD/base mismatch")
    if current_files != set(report["changed_files"]):
        errors.append(f"{case_id}: live changed files do not match the report")
    diff_check = git(worktree, "diff", "--check", "HEAD")
    if diff_check.returncode:
        errors.append(f"{case_id}: live git diff --check failed: {diff_check.stdout}{diff_check.stderr}")
    source_common = git(source, "rev-parse", "--git-common-dir")
    worktree_common = git(worktree, "rev-parse", "--git-common-dir")
    if source_common.returncode or worktree_common.returncode:
        errors.append(f"{case_id}: cannot verify worktree provenance")
    else:
        source_common_path = (source / source_common.stdout.strip()).resolve()
        worktree_common_path = (worktree / worktree_common.stdout.strip()).resolve()
        if source_common_path != worktree_common_path:
            errors.append(f"{case_id}: evaluation worktree is not attached to the source repository")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("report", type=pathlib.Path)
    parser.add_argument("--source-worktree", type=pathlib.Path)
    parser.add_argument(
        "--worktree", action="append", default=[], metavar="CASE_ID=PATH",
        help="live evaluation worktree for a case; requires --source-worktree",
    )
    args = parser.parse_args()

    live_worktrees: dict[str, pathlib.Path] = {}
    for item in args.worktree:
        case_id, separator, raw_path = item.partition("=")
        if not separator or not case_id or not raw_path or case_id in live_worktrees:
            parser.error("--worktree must be a unique CASE_ID=PATH mapping")
        live_worktrees[case_id] = pathlib.Path(raw_path)
    if bool(args.source_worktree) != bool(live_worktrees):
        parser.error("--source-worktree and at least one --worktree mapping are required together")

    cases = {item["id"]: item for item in load_jsonl(CASES)}
    reports = load_jsonl(args.report)
    evidence_root = args.report.resolve().parent if args.source_worktree else None
    errors: list[str] = []
    mapped: dict[str, dict] = {}

    for report in reports:
        case_id = report.get("case_id")
        if case_id in mapped:
            errors.append(f"duplicate report: {case_id}")
        mapped[case_id] = report
        case = cases.get(case_id)
        if case is None:
            errors.append(f"unknown case: {case_id}")
            continue
        expected_keys = {
            "run_id", "case_id", "repository", "base_commit", "branch",
            "source_status_before", "source_status_after", "changed_files",
            "red", "green", "regression", "diff_check", "scorecard",
        }
        if set(report) != expected_keys:
            errors.append(f"{case_id}: invalid report shape")
            continue
        if not isinstance(report["run_id"], str) or not report["run_id"].strip():
            errors.append(f"{case_id}: missing run_id")
        if report["repository"] != case["repository"] or report["branch"] != case["branch"]:
            errors.append(f"{case_id}: repository or branch mismatch")
        if not re.fullmatch(r"[0-9a-f]{40}", str(report["base_commit"])):
            errors.append(f"{case_id}: base_commit must be a full Git SHA")
        if not isinstance(report["source_status_before"], str) or not report["source_status_before"].strip():
            errors.append(f"{case_id}: source status fingerprint must be non-empty")
        elif report["source_status_before"] != report["source_status_after"]:
            errors.append(f"{case_id}: source worktree changed during evaluation")
        if not nonempty_strings(report["changed_files"]):
            errors.append(f"{case_id}: changed_files must be non-empty")
        elif not set(report["changed_files"]).issubset(set(case["allowed_paths"])):
            errors.append(f"{case_id}: changed file outside allowed paths")
        if not validate_command(report["red"], expect_success=False, evidence_root=evidence_root):
            errors.append(f"{case_id}: invalid red evidence")
        if not validate_command(report["green"], expect_success=True, evidence_root=evidence_root):
            errors.append(f"{case_id}: invalid green evidence")
        regression = report["regression"]
        if not isinstance(regression, list) or not regression or not all(
            validate_command(item, expect_success=True, evidence_root=evidence_root)
            for item in regression
        ):
            errors.append(f"{case_id}: invalid regression evidence")
        if not validate_command(report["diff_check"], expect_success=True, evidence_root=evidence_root):
            errors.append(f"{case_id}: invalid diff-check evidence")
        scorecard = report["scorecard"]
        if not isinstance(scorecard, dict):
            errors.append(f"{case_id}: scorecard must be an object")
        else:
            errors.extend(validate_scorecard(scorecard, f"{args.report}:{case_id}"))
            if scorecard.get("run_id") != report["run_id"] or scorecard.get("case_id") != case_id:
                errors.append(f"{case_id}: scorecard identity mismatch")
            if scorecard.get("artifact_type") != "code" or scorecard.get("decision") != "pass":
                errors.append(f"{case_id}: code scorecard did not pass")
        if args.source_worktree:
            worktree = live_worktrees.get(case_id)
            if worktree is None:
                errors.append(f"{case_id}: missing live worktree mapping")
            else:
                errors.extend(validate_live_state(report, args.source_worktree, worktree))

    if set(mapped) != set(cases):
        errors.append(f"coverage mismatch missing={sorted(set(cases) - set(mapped))} extra={sorted(set(mapped) - set(cases))}")
    if live_worktrees and set(live_worktrees) != set(cases):
        errors.append(f"live worktree coverage mismatch missing={sorted(set(cases) - set(live_worktrees))} extra={sorted(set(live_worktrees) - set(cases))}")
    scores = [item.get("scorecard", {}).get("total", 0) for item in reports if isinstance(item.get("scorecard"), dict)]
    if len(scores) == len(cases) and (min(scores) < 85 or sum(scores) / len(scores) < 90):
        errors.append("real-project quality threshold failed")
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"validated {len(reports)} real-project reports; average={sum(scores) / len(scores):.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
