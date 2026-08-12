#!/usr/bin/env python3
"""Prepare, verify, and aggregate reproducible blind generative evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
CASES_PATH = ROOT / "evals/cases/generative-cases.jsonl"
RUNS = ROOT / "evals/.runs"
DECISIONS = {"pass", "revise", "fail"}
PRIORITIES = {"P0", "P1", "P2", "P3"}
SNAPSHOT_SCHEMA_VERSION = 2
EXPECTED_SWIFT_TEST_COUNT = 20
EXPECTED_REDUCER_RED_TEST_COUNT = 1
EXPECTED_REDUCER_RED_TEST_NAME = "logged-out state rejects stale session events"
EXPECTED_BASELINE_DIAGNOSTICS = (
    "cannot find type 'AvatarUploadTask' in scope",
    "cannot find type 'CacheAtomicWriting' in scope",
    "cannot find 'SearchViewModel' in scope",
    "cannot find 'FileCacheStore' in scope",
    "cannot find 'LayoutConstraintPolicy' in scope",
    "cannot find 'RetryConfigurationLoader' in scope",
    "error: fatalError",
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
MERMAID_STARTS = (
    "flowchart ", "graph ", "sequenceDiagram", "stateDiagram", "classDiagram",
    "erDiagram", "journey", "gantt", "pie", "mindmap", "timeline",
)


def load_jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: pathlib.Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items), encoding="utf-8")


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(base: pathlib.Path, relative: object) -> pathlib.Path:
    if not isinstance(relative, str) or not relative:
        raise ValueError("evidence path must be a non-empty safe relative path")
    pure = pathlib.PurePosixPath(relative)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise ValueError(f"evidence path must be a safe relative path: {relative}")
    base_resolved = base.resolve()
    target = (base / pathlib.Path(*pure.parts)).resolve()
    try:
        target.relative_to(base_resolved)
    except ValueError as error:
        raise ValueError(f"evidence path must stay inside its root: {relative}") from error
    if not target.is_file() or (base / pathlib.Path(*pure.parts)).is_symlink():
        raise ValueError(f"evidence path is not a regular file: {relative}")
    return target


def sha256_record(path: pathlib.Path, base: pathlib.Path) -> dict[str, str]:
    base_resolved = base.resolve()
    target = path.resolve()
    try:
        relative = target.relative_to(base_resolved).as_posix()
    except ValueError as error:
        raise ValueError(f"evidence file is outside its root: {path}") from error
    if not target.is_file() or path.is_symlink():
        raise ValueError(f"evidence file is not a regular file: {path}")
    return {"path": relative, "sha256": sha256(target)}


def source_files(directory: pathlib.Path) -> list[pathlib.Path]:
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file()
        and not {".build", ".swiftpm"}.intersection(path.relative_to(directory).parts)
    )


def immutable_run_files(directory: pathlib.Path) -> list[pathlib.Path]:
    package = directory / "code-drills"
    reducer_red = directory / "reducer-red"
    return [
        directory / "blind-packets.jsonl",
        package / "Package.swift",
        *source_files(package / "Tests"),
        reducer_red / "Package.swift",
        *source_files(reducer_red / "Sources"),
        *source_files(reducer_red / "Tests"),
    ]


def baseline_fixture_files(package: pathlib.Path) -> list[pathlib.Path]:
    return [
        package / "Package.swift",
        *source_files(package / "Sources"),
        *source_files(package / "Tests"),
    ]


def reducer_red_fixture_files(package: pathlib.Path) -> list[pathlib.Path]:
    return [
        package / "Package.swift",
        *source_files(package / "Tests"),
    ]


def prepare_reducer_red_harness(
    directory: pathlib.Path,
    baseline_package: pathlib.Path,
    reducer_red_fixture: pathlib.Path | None = None,
) -> pathlib.Path:
    fixture = reducer_red_fixture or ROOT / "evals/fixtures/reducer-red"
    prepared = directory / "reducer-red"
    if prepared.exists():
        raise FileExistsError(f"focused reducer RED harness already exists: {prepared}")
    shutil.copytree(
        fixture,
        prepared,
        ignore=shutil.ignore_patterns(".build", ".swiftpm"),
    )
    destination = prepared / "Sources/CodeQualityDrills/Drills.swift"
    destination.parent.mkdir(parents=True)
    shutil.copy2(
        baseline_package / "Sources/CodeQualityDrills/Drills.swift",
        destination,
    )
    return prepared


def create_input_manifest(
    directory: pathlib.Path,
    baseline_package: pathlib.Path,
    run_id: str,
    reducer_red_fixture: pathlib.Path | None = None,
) -> dict:
    reducer_fixture = reducer_red_fixture or ROOT / "evals/fixtures/reducer-red"
    manifest = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "run_id": run_id,
        "run_inputs": [sha256_record(path, directory) for path in immutable_run_files(directory)],
        "baseline_fixture": [
            sha256_record(path, baseline_package) for path in baseline_fixture_files(baseline_package)
        ],
        "reducer_red_fixture": [
            sha256_record(path, reducer_fixture)
            for path in reducer_red_fixture_files(reducer_fixture)
        ],
    }
    (directory / "input-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def validate_record(record: object, base: pathlib.Path) -> pathlib.Path:
    if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
        raise ValueError("file record must contain exactly path and sha256")
    expected_hash = record.get("sha256")
    if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(expected_hash):
        raise ValueError("file record has an invalid SHA256")
    target = safe_relative_path(base, record.get("path"))
    if sha256(target) != expected_hash:
        raise ValueError(f"SHA256 mismatch for {record.get('path')}")
    return target


def validate_record_list(records: object, base: pathlib.Path, label: str) -> list[dict]:
    if not isinstance(records, list) or not records:
        raise ValueError(f"{label} must be a non-empty file-record list")
    paths = []
    for record in records:
        validate_record(record, base)
        paths.append(record["path"])
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError(f"{label} paths must be sorted and unique")
    return records


def validate_immutable_inputs(
    directory: pathlib.Path,
    baseline_package: pathlib.Path,
    expected_run_id: str,
    reducer_red_fixture: pathlib.Path | None = None,
) -> dict:
    reducer_fixture = reducer_red_fixture or ROOT / "evals/fixtures/reducer-red"
    try:
        manifest = json.loads((directory / "input-manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load immutable input manifest: {error}") from error
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version", "run_id", "run_inputs", "baseline_fixture",
        "reducer_red_fixture",
    }:
        raise ValueError("input manifest has an invalid schema")
    if manifest["schema_version"] != SNAPSHOT_SCHEMA_VERSION or manifest["run_id"] != expected_run_id:
        raise ValueError("input manifest identity mismatch")
    recorded_run = validate_record_list(manifest["run_inputs"], directory, "run_inputs")
    recorded_baseline = validate_record_list(
        manifest["baseline_fixture"], baseline_package, "baseline_fixture"
    )
    recorded_reducer_fixture = validate_record_list(
        manifest["reducer_red_fixture"], reducer_fixture, "reducer_red_fixture"
    )
    current_run = [sha256_record(path, directory) for path in immutable_run_files(directory)]
    current_baseline = [
        sha256_record(path, baseline_package) for path in baseline_fixture_files(baseline_package)
    ]
    current_reducer_fixture = [
        sha256_record(path, reducer_fixture)
        for path in reducer_red_fixture_files(reducer_fixture)
    ]
    if recorded_run != current_run:
        raise ValueError("immutable run input changed after prepare")
    if recorded_baseline != current_baseline:
        raise ValueError("baseline fixture changed after prepare")
    if recorded_reducer_fixture != current_reducer_fixture:
        raise ValueError("focused reducer RED fixture changed after prepare")

    baseline_by_path = {record["path"]: record["sha256"] for record in recorded_baseline}
    copied_by_path = {
        record["path"].removeprefix("code-drills/"): record["sha256"]
        for record in recorded_run if record["path"].startswith("code-drills/")
    }
    immutable_baseline = {
        path: digest for path, digest in baseline_by_path.items()
        if path == "Package.swift" or path.startswith("Tests/")
    }
    if copied_by_path != immutable_baseline:
        raise ValueError("run Package.swift or Tests do not match the baseline fixture")

    reducer_fixture_by_path = {
        record["path"]: record["sha256"] for record in recorded_reducer_fixture
    }
    prepared_reducer_by_path = {
        record["path"].removeprefix("reducer-red/"): record["sha256"]
        for record in recorded_run if record["path"].startswith("reducer-red/")
    }
    baseline_source = baseline_by_path.get("Sources/CodeQualityDrills/Drills.swift")
    expected_reducer_files = {
        **reducer_fixture_by_path,
        "Sources/CodeQualityDrills/Drills.swift": baseline_source,
    }
    if prepared_reducer_by_path != expected_reducer_files:
        raise ValueError(
            "focused reducer source and harness must exactly match their immutable fixtures"
        )
    return manifest


def run_dir(run_id: str) -> pathlib.Path:
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", run_id):
        raise ValueError("run_id must be a safe 1-80 character identifier")
    return RUNS / run_id


def prepare(run_id: str) -> None:
    directory = run_dir(run_id)
    if directory.exists():
        raise FileExistsError(f"run already exists: {directory}")
    cases = load_jsonl(CASES_PATH)
    packets = []
    for case in cases:
        # Acceptance criteria are part of the task contract, not a hidden answer.
        # Give them to both the implementer and blind graders so scope cannot be
        # silently reduced to whatever the smallest fixture happens to cover.
        packet = {key: case[key] for key in ("id", "artifact_type", "prompt", "acceptance")}
        if case["artifact_type"] == "code":
            packet.update({
                "fixture": "code-drills",
                "drill": int(case["id"].rsplit("-", 1)[1]),
                "test_command": "swift test",
            })
        packets.append(packet)
    write_jsonl(directory / "blind-packets.jsonl", packets)
    fixture_source = ROOT / "evals/fixtures/code-drills"
    shutil.copytree(
        fixture_source,
        directory / "code-drills",
        ignore=shutil.ignore_patterns(".build", ".swiftpm"),
    )
    prepare_reducer_red_harness(directory, fixture_source)
    (directory / "artifacts").mkdir()
    create_input_manifest(directory, fixture_source, run_id)
    print(directory)


def mermaid_blocks(text: str) -> list[str]:
    return re.findall(r"```mermaid\s*\n(.*?)```", text, flags=re.DOTALL)


def has_markdown_table(text: str) -> bool:
    lines = text.splitlines()
    return any(
        index > 0
        and line.strip().startswith("|")
        and re.fullmatch(r"\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*", line)
        and lines[index - 1].strip().startswith("|")
        for index, line in enumerate(lines)
    )


def validate_mermaid(block: str, case_id: str) -> list[str]:
    errors: list[str] = []
    content = block.strip()
    if not content.startswith(MERMAID_STARTS):
        errors.append(f"{case_id}: unsupported or missing Mermaid diagram declaration")
    if content.count('"') % 2:
        errors.append(f"{case_id}: Mermaid contains an unbalanced quote")
    if not any(token in content for token in ("-->", "->>", "-->>", ":")):
        errors.append(f"{case_id}: Mermaid has no observable relationship or transition")
    return errors


def write_command_log(
    path: pathlib.Path,
    command: list[str],
    exit_code: int,
    stdout: str,
    stderr: str,
) -> None:
    path.write_text(
        f"command: {' '.join(command)}\nexit_code: {exit_code}\n" + stdout + stderr,
        encoding="utf-8",
    )


def declared_swift_test_count(path: pathlib.Path) -> int:
    return len(re.findall(r"(?m)^\s*@Test(?:\(|\s*$)", path.read_text(encoding="utf-8")))


def baseline_has_expected_red(text: str) -> bool:
    return all(marker in text for marker in EXPECTED_BASELINE_DIAGNOSTICS)


def reducer_red_has_expected_failure(text: str) -> bool:
    return (
        EXPECTED_REDUCER_RED_TEST_NAME in text
        and "stale" in text
        and log_has_test_summary(text, EXPECTED_REDUCER_RED_TEST_COUNT, "failed")
    )


def log_has_test_summary(text: str, count: int, outcome: str) -> bool:
    return bool(re.search(
        rf"Test run with {count} tests? in \d+ suites? {re.escape(outcome)}(?:\s|$)",
        text,
    ))


def verify_artifacts(run_id: str, mermaid_cli: pathlib.Path | None = None) -> None:
    directory = run_dir(run_id)
    baseline_package = ROOT / "evals/fixtures/code-drills"
    try:
        input_manifest = validate_immutable_inputs(directory, baseline_package, run_id)
    except ValueError as error:
        print(f"ERROR code-drills: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    packets = load_jsonl(directory / "blind-packets.jsonl")
    errors: list[str] = []
    render_jobs: list[tuple[str, int, str]] = []
    artifact_paths: list[pathlib.Path] = []
    for case in packets:
        path = directory / "artifacts" / f"{case['id']}.md"
        if not path.is_file() or not path.read_text(encoding="utf-8").strip():
            errors.append(f"{case['id']}: missing non-empty artifact")
            continue
        artifact_paths.append(path)
        text = path.read_text(encoding="utf-8")
        blocks = mermaid_blocks(text)
        if case["artifact_type"] == "diagram_required" and not blocks and not has_markdown_table(text):
            errors.append(f"{case['id']}: required explanatory diagram or comparison table is missing")
        if case["artifact_type"] == "diagram_not_needed" and blocks:
            errors.append(f"{case['id']}: unnecessary Mermaid diagram is present")
        for block in blocks:
            errors.extend(validate_mermaid(block, case["id"]))
        render_jobs.extend((case["id"], index, block) for index, block in enumerate(blocks, start=1))
        if case["artifact_type"] == "code" and "```swift" not in text:
            errors.append(f"{case['id']}: code artifact lacks a Swift excerpt")
    package = directory / "code-drills"
    baseline_command = ["swift", "test", "--package-path", str(baseline_package)]
    baseline = subprocess.run(
        baseline_command,
        capture_output=True, text=True,
        env={
            **os.environ,
            "CLANG_MODULE_CACHE_PATH": "/private/tmp/codex-personal-skills-clang-cache",
            "SWIFTPM_MODULECACHE_OVERRIDE": "/private/tmp/codex-personal-skills-swiftpm-cache",
        },
    )
    baseline_log = directory / "baseline-red.log"
    write_command_log(
        baseline_log, baseline_command, baseline.returncode, baseline.stdout, baseline.stderr
    )
    baseline_text = baseline_log.read_text(encoding="utf-8")
    if baseline.returncode == 0 or not baseline_has_expected_red(baseline_text):
        errors.append(f"code-drills: baseline did not produce the expected test failure; see {baseline_log}")
    reducer_red_package = directory / "reducer-red"
    reducer_red_command = ["swift", "test", "--package-path", str(reducer_red_package)]
    reducer_red = subprocess.run(
        reducer_red_command,
        capture_output=True, text=True,
        env={
            **os.environ,
            "CLANG_MODULE_CACHE_PATH": "/private/tmp/codex-personal-skills-clang-cache",
            "SWIFTPM_MODULECACHE_OVERRIDE": "/private/tmp/codex-personal-skills-swiftpm-cache",
        },
    )
    reducer_red_log = directory / "reducer-red.log"
    write_command_log(
        reducer_red_log,
        reducer_red_command,
        reducer_red.returncode,
        reducer_red.stdout,
        reducer_red.stderr,
    )
    reducer_red_text = reducer_red_log.read_text(encoding="utf-8")
    if reducer_red.returncode == 0 or not reducer_red_has_expected_failure(reducer_red_text):
        errors.append(
            "code-drills: focused reducer harness did not produce the expected stale-session "
            f"runtime RED; see {reducer_red_log}"
        )
    test_log = directory / "swift-test.log"
    test_command = ["swift", "test", "--package-path", str(package)]
    result = subprocess.run(
        test_command,
        capture_output=True, text=True,
        env={
            **os.environ,
            "CLANG_MODULE_CACHE_PATH": "/private/tmp/codex-personal-skills-clang-cache",
            "SWIFTPM_MODULECACHE_OVERRIDE": "/private/tmp/codex-personal-skills-swiftpm-cache",
        },
    )
    write_command_log(test_log, test_command, result.returncode, result.stdout, result.stderr)
    test_text = test_log.read_text(encoding="utf-8")
    if (
        declared_swift_test_count(package / "Tests/CodeQualityDrillsTests/DrillsTests.swift")
        != EXPECTED_SWIFT_TEST_COUNT
        or result.returncode
        or not log_has_test_summary(
        test_text, EXPECTED_SWIFT_TEST_COUNT, "passed"
        )
    ):
        errors.append(f"code-drills: swift test failed; see {test_log}")
    ios_log = directory / "ios-typecheck.log"
    sdk_command = ["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"]
    sdk = subprocess.run(
        sdk_command,
        capture_output=True, text=True,
    )
    if sdk.returncode:
        ios_command = sdk_command
        ios_exit_code = sdk.returncode
        write_command_log(ios_log, ios_command, ios_exit_code, sdk.stdout, sdk.stderr)
        errors.append(f"code-drills: cannot resolve iOS Simulator SDK; see {ios_log}")
    else:
        ios_command = [
                "xcrun", "swiftc", "-typecheck", "-parse-as-library",
                "-swift-version", "6", "-target", "arm64-apple-ios17.0-simulator",
                "-sdk", sdk.stdout.strip(),
                str(package / "Sources/CodeQualityDrills/Drills.swift"),
        ]
        ios_check = subprocess.run(
            ios_command,
            capture_output=True, text=True,
        )
        ios_exit_code = ios_check.returncode
        write_command_log(
            ios_log, ios_command, ios_exit_code, ios_check.stdout, ios_check.stderr
        )
        if ios_exit_code:
            errors.append(f"code-drills: iOS 17 Simulator typecheck failed; see {ios_log}")
    rendered_outputs: list[pathlib.Path] = []
    if mermaid_cli is not None:
        if not mermaid_cli.is_file():
            errors.append(f"Mermaid CLI does not exist: {mermaid_cli}")
        else:
            render_dir = directory / "mermaid-render"
            render_dir.mkdir(exist_ok=True)
            for case_id, index, block in render_jobs:
                source = render_dir / f"{case_id}-{index}.mmd"
                output = render_dir / f"{case_id}-{index}.svg"
                source.write_text(block.strip() + "\n", encoding="utf-8")
                rendered = subprocess.run(
                    [str(mermaid_cli), "-i", str(source), "-o", str(output), "--quiet"],
                    capture_output=True, text=True,
                )
                if rendered.returncode or not output.is_file() or output.stat().st_size == 0:
                    detail = (rendered.stdout + rendered.stderr).strip()
                    errors.append(f"{case_id}: Mermaid render failed: {detail[-500:]}")
                else:
                    rendered_outputs.append(output)
    verification = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "run_id": run_id,
        "inputs": {
            "manifest": sha256_record(directory / "input-manifest.json", directory),
            "files": input_manifest["run_inputs"],
        },
        "artifacts": [sha256_record(path, directory) for path in sorted(artifact_paths)],
        "baseline": {
            "command": baseline_command,
            "exit_code": baseline.returncode,
            "expected_diagnostics": list(EXPECTED_BASELINE_DIAGNOSTICS),
            "log": sha256_record(baseline_log, directory),
        },
        "reducer_red": {
            "command": reducer_red_command,
            "exit_code": reducer_red.returncode,
            "expected_test_name": EXPECTED_REDUCER_RED_TEST_NAME,
            "expected_test_count": EXPECTED_REDUCER_RED_TEST_COUNT,
            "source": sha256_record(
                reducer_red_package / "Sources/CodeQualityDrills/Drills.swift",
                directory,
            ),
            "log": sha256_record(reducer_red_log, directory),
        },
        "swift_test": {
            "command": test_command,
            "exit_code": result.returncode,
            "expected_test_count": EXPECTED_SWIFT_TEST_COUNT,
            "log": sha256_record(test_log, directory),
        },
        "ios_typecheck": {
            "command": ios_command,
            "exit_code": ios_exit_code,
            "log": sha256_record(ios_log, directory),
        },
        "mermaid": {
            "requested": mermaid_cli is not None,
            "source_blocks": len(render_jobs),
            "rendered_count": len(rendered_outputs),
            "outputs": [sha256_record(path, directory) for path in sorted(rendered_outputs)],
        },
    }
    (directory / "verification.json").write_text(
        json.dumps(verification, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        raise SystemExit(1)
    print(f"verified {len(packets)} artifacts; swift test passed")


def validate_grader(path: pathlib.Path, case_ids: set[str]) -> dict[str, dict]:
    rows = load_jsonl(path)
    errors: list[str] = []
    mapped: dict[str, dict] = {}
    for row in rows:
        if set(row) != {"grader_id", "case_id", "score", "decision", "evidence", "issues"}:
            errors.append(f"{path}: invalid row shape")
            continue
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{path}: case_id must be a non-empty string")
            continue
        if case_id in mapped:
            errors.append(f"{path}: duplicate case {case_id}")
        mapped[case_id] = row
        if not isinstance(row.get("grader_id"), str) or not row["grader_id"].strip():
            errors.append(f"{path}:{case_id}: missing grader_id")
        if not isinstance(row.get("score"), int) or isinstance(row.get("score"), bool) or not 0 <= row["score"] <= 100:
            errors.append(f"{path}:{case_id}: invalid score")
        if row.get("decision") not in DECISIONS:
            errors.append(f"{path}:{case_id}: invalid decision")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence or not all(isinstance(item, str) and item.strip() for item in evidence):
            errors.append(f"{path}:{case_id}: evidence must be non-empty strings")
        issues = row.get("issues")
        if not isinstance(issues, list):
            errors.append(f"{path}:{case_id}: issues must be an array")
        else:
            for issue in issues:
                if not isinstance(issue, dict) or set(issue) != {"priority", "message"} or issue.get("priority") not in PRIORITIES or not str(issue.get("message", "")).strip():
                    errors.append(f"{path}:{case_id}: invalid issue")
    if set(mapped) != case_ids:
        errors.append(f"{path}: coverage mismatch missing={sorted(case_ids - set(mapped))} extra={sorted(set(mapped) - case_ids)}")
    grader_ids = {
        row.get("grader_id") for row in mapped.values()
        if isinstance(row.get("grader_id"), str) and row["grader_id"].strip()
    }
    if len(grader_ids) != 1:
        errors.append(f"{path}: every row must use one consistent grader_id")
    if errors:
        raise ValueError("\n".join(errors))
    return mapped


def validate_independent_graders(
    grader_paths: list[pathlib.Path],
    case_ids: set[str],
) -> list[dict[str, dict]]:
    if len(grader_paths) != 2:
        raise ValueError("exactly two independent grader files are required")
    resolved_paths = [path.resolve() for path in grader_paths]
    if resolved_paths[0] == resolved_paths[1]:
        raise ValueError("independent graders must use two different files")
    graders = [validate_grader(path, case_ids) for path in grader_paths]
    grader_ids = [next(iter({row["grader_id"] for row in grader.values()})) for grader in graders]
    if grader_ids[0] == grader_ids[1]:
        raise ValueError("independent graders must use distinct grader_id values")
    return graders


def validate_command_section(
    section: object,
    directory: pathlib.Path,
    label: str,
    expected_keys: set[str],
) -> tuple[list[str], int, pathlib.Path, str]:
    if not isinstance(section, dict) or set(section) != expected_keys:
        raise ValueError(f"{label} has an invalid schema")
    command = section.get("command")
    if not isinstance(command, list) or not command or not all(
        isinstance(item, str) and item for item in command
    ):
        raise ValueError(f"{label} command must be a non-empty string list")
    exit_code = section.get("exit_code")
    if not isinstance(exit_code, int) or isinstance(exit_code, bool):
        raise ValueError(f"{label} exit_code must be an integer")
    log_path = validate_record(section.get("log"), directory)
    log_text = log_path.read_text(encoding="utf-8")
    expected_header = f"command: {' '.join(command)}\nexit_code: {exit_code}\n"
    if not log_text.startswith(expected_header):
        raise ValueError(f"{label} log does not match its command and exit_code")
    return command, exit_code, log_path, log_text


def validate_verification_snapshot(
    directory: pathlib.Path,
    *,
    expected_run_id: str | None = None,
    baseline_package: pathlib.Path | None = None,
    reducer_red_fixture: pathlib.Path | None = None,
) -> None:
    directory = directory.resolve()
    path = directory / "verification.json"
    try:
        snapshot = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot load verified run snapshot: {error}") from error
    expected_snapshot_keys = {
        "schema_version", "run_id", "inputs", "artifacts", "baseline",
        "reducer_red", "swift_test", "ios_typecheck", "mermaid",
    }
    if not isinstance(snapshot, dict) or set(snapshot) != expected_snapshot_keys:
        raise ValueError("verification snapshot has an invalid schema")
    if snapshot["schema_version"] != SNAPSHOT_SCHEMA_VERSION:
        raise ValueError("verification snapshot schema version mismatch")
    run_id = snapshot.get("run_id")
    if not isinstance(run_id, str) or not run_id or (
        expected_run_id is not None and run_id != expected_run_id
    ):
        raise ValueError("verification snapshot run_id mismatch")

    baseline_root = (baseline_package or ROOT / "evals/fixtures/code-drills").resolve()
    manifest = validate_immutable_inputs(
        directory,
        baseline_root,
        run_id,
        reducer_red_fixture,
    )
    inputs = snapshot.get("inputs")
    if not isinstance(inputs, dict) or set(inputs) != {"manifest", "files"}:
        raise ValueError("verification snapshot inputs have an invalid schema")
    validate_record(inputs["manifest"], directory)
    if inputs["manifest"] != sha256_record(directory / "input-manifest.json", directory):
        raise ValueError("verification snapshot input manifest record mismatch")
    validate_record_list(inputs["files"], directory, "snapshot input files")
    if inputs["files"] != manifest["run_inputs"]:
        raise ValueError("verification snapshot input files do not match prepare")

    packets = load_jsonl(directory / "blind-packets.jsonl")
    expected_artifact_paths = sorted(
        directory / "artifacts" / f"{case['id']}.md" for case in packets
    )
    expected_artifacts = [sha256_record(item, directory) for item in expected_artifact_paths]
    validate_record_list(snapshot["artifacts"], directory, "snapshot artifacts")
    if snapshot["artifacts"] != expected_artifacts:
        raise ValueError("verification snapshot artifact manifest mismatch")

    baseline_command, baseline_exit, _, baseline_text = validate_command_section(
        snapshot["baseline"], directory, "baseline",
        {"command", "exit_code", "expected_diagnostics", "log"},
    )
    expected_baseline_command = ["swift", "test", "--package-path", str(baseline_root)]
    if baseline_command != expected_baseline_command:
        raise ValueError("baseline command does not target the immutable fixture")
    if snapshot["baseline"]["expected_diagnostics"] != list(EXPECTED_BASELINE_DIAGNOSTICS):
        raise ValueError("baseline diagnostic contract mismatch")
    if baseline_exit == 0 or not baseline_has_expected_red(baseline_text):
        raise ValueError("baseline must contain the expected compile-time RED diagnostics")

    reducer_command, reducer_exit, _, reducer_text = validate_command_section(
        snapshot["reducer_red"], directory, "reducer_red",
        {
            "command", "exit_code", "expected_test_name", "expected_test_count",
            "source", "log",
        },
    )
    expected_reducer_command = [
        "swift", "test", "--package-path", str(directory / "reducer-red")
    ]
    if reducer_command != expected_reducer_command:
        raise ValueError("focused reducer RED command does not target the prepared harness")
    if (
        snapshot["reducer_red"]["expected_test_name"] != EXPECTED_REDUCER_RED_TEST_NAME
        or snapshot["reducer_red"]["expected_test_count"] != EXPECTED_REDUCER_RED_TEST_COUNT
    ):
        raise ValueError("focused reducer RED test contract mismatch")
    reducer_source = directory / "reducer-red/Sources/CodeQualityDrills/Drills.swift"
    validate_record(snapshot["reducer_red"]["source"], directory)
    if snapshot["reducer_red"]["source"] != sha256_record(reducer_source, directory):
        raise ValueError("focused reducer source record mismatch")
    baseline_sources = {
        record["path"]: record["sha256"] for record in manifest["baseline_fixture"]
    }
    if sha256(reducer_source) != baseline_sources["Sources/CodeQualityDrills/Drills.swift"]:
        raise ValueError("focused reducer source does not match the immutable baseline source")
    if reducer_exit == 0 or not reducer_red_has_expected_failure(reducer_text):
        raise ValueError("focused reducer RED evidence does not show the stale-session failure")

    swift_command, swift_exit, _, swift_text = validate_command_section(
        snapshot["swift_test"], directory, "swift_test",
        {"command", "exit_code", "expected_test_count", "log"},
    )
    expected_swift_command = [
        "swift", "test", "--package-path", str(directory / "code-drills")
    ]
    if swift_command != expected_swift_command:
        raise ValueError("final Swift command does not target the prepared run package")
    if snapshot["swift_test"]["expected_test_count"] != EXPECTED_SWIFT_TEST_COUNT:
        raise ValueError("final Swift test count contract mismatch")
    test_source = directory / "code-drills/Tests/CodeQualityDrillsTests/DrillsTests.swift"
    if declared_swift_test_count(test_source) != EXPECTED_SWIFT_TEST_COUNT:
        raise ValueError("immutable Swift suite does not declare twenty tests")
    if swift_exit != 0 or not log_has_test_summary(
        swift_text, EXPECTED_SWIFT_TEST_COUNT, "passed"
    ):
        raise ValueError("final Swift test must pass the immutable twenty-test suite")

    ios_command, ios_exit, _, _ = validate_command_section(
        snapshot["ios_typecheck"], directory, "ios_typecheck",
        {"command", "exit_code", "log"},
    )
    expected_source = str(
        directory / "code-drills/Sources/CodeQualityDrills/Drills.swift"
    )
    if ios_command[:3] != ["xcrun", "swiftc", "-typecheck"] or ios_command[-1] != expected_source:
        raise ValueError("iOS typecheck command does not target the prepared source")
    if ios_exit != 0:
        raise ValueError("iOS Simulator typecheck must pass")

    mermaid = snapshot.get("mermaid")
    if not isinstance(mermaid, dict) or set(mermaid) != {
        "requested", "source_blocks", "rendered_count", "outputs",
    }:
        raise ValueError("verification snapshot Mermaid section has an invalid schema")
    artifact_blocks = [
        (case["id"], index)
        for case in packets
        for index, _ in enumerate(
            mermaid_blocks((directory / "artifacts" / f"{case['id']}.md").read_text(encoding="utf-8")),
            start=1,
        )
    ]
    expected_output_paths = sorted(
        directory / "mermaid-render" / f"{case_id}-{index}.svg"
        for case_id, index in artifact_blocks
    )
    expected_outputs = [sha256_record(path, directory) for path in expected_output_paths]
    if mermaid["requested"] is not True:
        raise ValueError("Mermaid rendering must be requested before aggregation")
    if (
        mermaid["source_blocks"] != len(artifact_blocks)
        or mermaid["rendered_count"] != len(artifact_blocks)
    ):
        raise ValueError("every Mermaid source block must render")
    if artifact_blocks:
        validate_record_list(mermaid["outputs"], directory, "Mermaid outputs")
    elif mermaid["outputs"] != []:
        raise ValueError("Mermaid outputs must be empty when no source blocks exist")
    if mermaid["outputs"] != expected_outputs:
        raise ValueError("Mermaid output manifest does not match artifact blocks")


def aggregate(run_id: str, grader_paths: list[pathlib.Path], adjudicator: pathlib.Path | None) -> None:
    directory = run_dir(run_id)
    validate_verification_snapshot(directory, expected_run_id=run_id)
    case_ids = {case["id"] for case in load_jsonl(directory / "blind-packets.jsonl")}
    graders = validate_independent_graders(grader_paths, case_ids)
    disagreements = []
    for case_id in sorted(case_ids):
        left, right = graders[0][case_id], graders[1][case_id]
        if abs(left["score"] - right["score"]) > 10 or left["decision"] != right["decision"]:
            disagreements.append({
                "case_id": case_id,
                "grader_a": {"score": left["score"], "decision": left["decision"]},
                "grader_b": {"score": right["score"], "decision": right["decision"]},
            })
    required_path = directory / "adjudication-required.json"
    required_path.write_text(json.dumps(disagreements, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if disagreements and adjudicator is None:
        print(f"adjudication required for {len(disagreements)} case(s): {required_path}", file=sys.stderr)
        raise SystemExit(2)
    adjudicated = validate_grader(adjudicator, {item["case_id"] for item in disagreements}) if disagreements else {}
    finals = []
    for case_id in sorted(case_ids):
        if case_id in adjudicated:
            final = adjudicated[case_id]
        else:
            left, right = graders[0][case_id], graders[1][case_id]
            final = {
                "case_id": case_id,
                "score": round((left["score"] + right["score"]) / 2),
                "decision": left["decision"],
                "issues": left["issues"] + right["issues"],
            }
        finals.append(final)
    average = sum(item["score"] for item in finals) / len(finals)
    security_failures = [item for item in finals if any(issue.get("priority") in {"P0", "P1"} for issue in item.get("issues", []))]
    passed = average >= 90 and all(item["decision"] == "pass" for item in finals) and not security_failures
    summary = {"run_id": run_id, "average": average, "passed": passed, "results": finals}
    (directory / "aggregate.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"average={average:.2f} passed={str(passed).lower()}")
    if not passed:
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    prepare_parser = sub.add_parser("prepare")
    prepare_parser.add_argument("run_id")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("run_id")
    verify_parser.add_argument("--mermaid-cli", type=pathlib.Path, help="render every Mermaid block with this mmdc binary")
    aggregate_parser = sub.add_parser("aggregate")
    aggregate_parser.add_argument("run_id")
    aggregate_parser.add_argument("graders", nargs=2, type=pathlib.Path)
    aggregate_parser.add_argument("--adjudicator", type=pathlib.Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.run_id)
    elif args.command == "verify":
        verify_artifacts(args.run_id, args.mermaid_cli)
    else:
        aggregate(args.run_id, args.graders, args.adjudicator)


if __name__ == "__main__":
    main()
