#!/usr/bin/env python3
"""Run deterministic repository checks for the personal Skill collection."""

from __future__ import annotations

import collections
import json
import pathlib
import re
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
SKILLS = ROOT / "skills"
REQUIRED_SKILLS = {
    "development-workflow", "developer-notes", "pr-review-to-notion",
    "ios-accessibility", "swift-concurrency", "swift-testing", "swiftui-uikit-interop",
    "android-kotlin-mvvm",
}
EXPECTED_BEHAVIOR_COUNTS = {
    "developer_notes": 25,
    "development_workflow": 15,
    "ios_routing": 10,
    "android_routing": 15,
    "pr_notion": 8,
    "security_conflict": 6,
}
EXPECTED_GENERATIVE_COUNTS = {
    "code": 8,
    "note": 13,
    "diagram_required": 4,
    "diagram_not_needed": 4,
}


def jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def check_case_rows(cases: list[dict], required_keys: set[str], label: str, errors: list[str]) -> None:
    ids = [case.get("id") for case in cases]
    if not all(isinstance(case_id, str) and case_id.strip() for case_id in ids):
        errors.append(f"{label} cases require non-empty string ids")
    elif len(set(ids)) != len(ids):
        errors.append(f"{label} case ids must be unique")
    for case in cases:
        if set(case) != required_keys:
            errors.append(f"{label} case has invalid shape: {case.get('id')}")
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"{label} case has empty prompt: {case.get('id')}")


def check_frontmatter(skill_dir: pathlib.Path, errors: list[str]) -> None:
    path = skill_dir / "SKILL.md"
    if not path.is_file():
        errors.append(f"missing {path.relative_to(ROOT)}")
        return
    text = path.read_text(encoding="utf-8")
    match = re.match(r"---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        errors.append(f"invalid frontmatter: {path.relative_to(ROOT)}")
        return
    keys = [line.split(":", 1)[0].strip() for line in match.group(1).splitlines() if ":" in line]
    if keys != ["name", "description"]:
        errors.append(f"frontmatter keys must be name, description: {path.relative_to(ROOT)}")
    if f"name: {skill_dir.name}\n" not in match.group(0):
        errors.append(f"skill name does not match folder: {skill_dir.name}")
    agent = skill_dir / "agents" / "openai.yaml"
    if not agent.is_file():
        errors.append(f"missing agents/openai.yaml: {skill_dir.name}")
    else:
        agent_text = agent.read_text(encoding="utf-8")
        for key in ("display_name:", "short_description:", "default_prompt:"):
            if key not in agent_text:
                errors.append(f"{skill_dir.name}: openai.yaml missing {key}")
    for reference in re.findall(r"`((?:\.\./development-workflow/)?(?:references|scripts)/[^` <>]+)`", text):
        if not (skill_dir / reference).resolve().is_file():
            errors.append(f"broken resource reference in {skill_dir.name}: {reference}")


def main() -> int:
    errors: list[str] = []
    actual_skills = {path.name for path in SKILLS.iterdir() if path.is_dir()}
    missing = REQUIRED_SKILLS - actual_skills
    if missing:
        errors.append(f"missing skills: {sorted(missing)}")
    for name in sorted(REQUIRED_SKILLS & actual_skills):
        check_frontmatter(SKILLS / name, errors)
    critical_rules = {
        SKILLS / "developer-notes/SKILL.md": (
            "does not authorize running repository tests",
            "The presence of a test file proves intended coverage, not that the test passed",
            "A template, traceability row, quality gate, or specialist Skill never expands command authorization",
        ),
        SKILLS / "development-workflow/SKILL.md": (
            "Documentation-only",
            "Project validation commands in this section apply only to an authorized code change or an explicit validation request",
            "/Users/admin/project/siuper-sdk-android",
            "/Users/admin/Desktop/project/siuper-ios",
            "These paths are location hints, not permission or a reason to load both repositories",
            "Minimal\u201d means no unrelated scope or unnecessary mechanism, not the fewest changed lines or files",
        ),
        SKILLS / "android-kotlin-mvvm/SKILL.md": (
            "A standalone note or documentation request authorizes inspection of code, tests, and existing reports only",
            "Do not launch multiple Gradle processes concurrently against the same checkout",
        ),
        SKILLS / "development-workflow/references/artifact-quality.md": (
            "it never authorizes project commands to create fresher evidence",
            "A test source alone must not be described as passing evidence",
            "project validation commands launched from documentation-only work without explicit authorization",
            "Do not reward a smaller diff when it omits work required by the accepted behavior or root cause",
        ),
        SKILLS / "development-workflow/references/project-locations.md": (
            "Do not open the counterpart repository merely because it is available",
            "read-only evidence source",
            "Do not run builds, tests, dependency resolution, generators, indexers, or broad Git-history searches",
        ),
    }
    for path, needles in critical_rules.items():
        source = path.read_text(encoding="utf-8")
        for needle in needles:
            if needle not in source:
                errors.append(f"missing command-authorization rule in {path.relative_to(ROOT)}: {needle}")
    behavior = jsonl(ROOT / "evals/cases/behavior-cases.jsonl")
    check_case_rows(behavior, {"id", "category", "prompt", "expected"}, "behavior", errors)
    counts = collections.Counter(case.get("category") for case in behavior)
    if len(behavior) != 79 or dict(counts) != EXPECTED_BEHAVIOR_COUNTS:
        errors.append(f"behavior case counts differ: total={len(behavior)} counts={dict(counts)}")
    generative = jsonl(ROOT / "evals/cases/generative-cases.jsonl")
    check_case_rows(generative, {"id", "artifact_type", "prompt", "acceptance"}, "generative", errors)
    if any(not isinstance(case.get("acceptance"), list) or not case["acceptance"] for case in generative):
        errors.append("every generative case needs acceptance criteria")
    gen_counts = collections.Counter(case.get("artifact_type") for case in generative)
    if dict(gen_counts) != EXPECTED_GENERATIVE_COUNTS:
        errors.append(f"generative case counts differ: {dict(gen_counts)}")
    real_project = jsonl(ROOT / "evals/cases/real-project-cases.jsonl")
    check_case_rows(
        real_project,
        {"id", "repository", "branch", "prompt", "allowed_paths", "acceptance"},
        "real-project",
        errors,
    )
    if len(real_project) != 2 or {case.get("repository") for case in real_project} != {"siuper-ios"}:
        errors.append("real-project evaluation must contain two siuper-ios cases")
    for executable in (
        "run_generative_eval.py", "run_behavior_eval.py", "run_android_eval.py", "validate_scorecard.py",
        "validate_real_project_report.py", "test_select_diff_evidence.py",
        "test_generative_verification.py", "test_pr_review_safety.py",
        "test_real_project_live_validation.py",
    ):
        if not (ROOT / "evals/scripts" / executable).is_file():
            errors.append(f"missing executable evaluator: {executable}")
    for fixture in (
        "Package.swift",
        "Sources/CodeQualityDrills/Drills.swift",
        "Tests/CodeQualityDrillsTests/DrillsTests.swift",
    ):
        if not (ROOT / "evals/fixtures/code-drills" / fixture).is_file():
            errors.append(f"missing code drill fixture: {fixture}")
    for fixture in (
        "Package.swift",
        "Tests/ReducerRedTests/ReducerRedTests.swift",
    ):
        if not (ROOT / "evals/fixtures/reducer-red" / fixture).is_file():
            errors.append(f"missing focused reducer RED fixture: {fixture}")
    drill_tests = ROOT / "evals/fixtures/code-drills/Tests/CodeQualityDrillsTests/DrillsTests.swift"
    if drill_tests.is_file():
        declared_tests = len(re.findall(r"(?m)^\s*@Test(?:\(|\s*$)", drill_tests.read_text(encoding="utf-8")))
        if declared_tests != 20:
            errors.append(f"code drill fixture must declare 20 immutable tests, found {declared_tests}")
    for required_text in (
        SKILLS / "development-workflow/references/artifact-quality.md",
        SKILLS / "development-workflow/SKILL.md",
        SKILLS / "developer-notes/SKILL.md",
    ):
        if "artifact-quality.md" not in required_text.read_text(encoding="utf-8") and required_text.name == "SKILL.md":
            errors.append(f"quality gate is not referenced by {required_text.relative_to(ROOT)}")
    validator = ROOT / "evals/scripts/validate_scorecard.py"
    valid = subprocess.run(
        [sys.executable, str(validator), "--suite",
         str(ROOT / "evals/fixtures/pass-code.json"),
         str(ROOT / "evals/fixtures/pass-note.json"),
         str(ROOT / "evals/fixtures/pass-workflow.json")],
        capture_output=True, text=True,
    )
    if valid.returncode:
        errors.append(f"valid scorecards rejected: {valid.stderr.strip()}")
    invalid = subprocess.run(
        [sys.executable, str(validator), str(ROOT / "evals/fixtures/invalid-pass.json")],
        capture_output=True, text=True,
    )
    if invalid.returncode == 0:
        errors.append("invalid passing scorecard was accepted")
    empty_evidence = subprocess.run(
        [sys.executable, str(validator), str(ROOT / "evals/fixtures/invalid-empty-evidence.json")],
        capture_output=True, text=True,
    )
    if empty_evidence.returncode == 0:
        errors.append("scorecard with empty evidence was accepted")
    empty_suite = subprocess.run(
        [sys.executable, str(validator), "--suite", str(ROOT / "evals/fixtures/empty-suite.json")],
        capture_output=True, text=True,
    )
    if empty_suite.returncode == 0:
        errors.append("empty scorecard suite was accepted")
    masked_average = subprocess.run(
        [sys.executable, str(validator), "--suite", str(ROOT / "evals/fixtures/invalid-masked-average.json")],
        capture_output=True, text=True,
    )
    if masked_average.returncode == 0:
        errors.append("low per-type suite average was masked by another artifact type")
    third_revise = subprocess.run(
        [sys.executable, str(validator), str(ROOT / "evals/fixtures/invalid-third-revise.json")],
        capture_output=True, text=True,
    )
    if third_revise.returncode == 0:
        errors.append("third unsuccessful attempt was allowed to remain revise")
    real_validator = ROOT / "evals/scripts/validate_real_project_report.py"
    valid_real = subprocess.run(
        [sys.executable, str(real_validator), str(ROOT / "evals/fixtures/pass-real-project-report.jsonl")],
        capture_output=True, text=True,
    )
    if valid_real.returncode:
        errors.append(f"valid real-project report rejected: {valid_real.stderr.strip()}")
    invalid_real = subprocess.run(
        [sys.executable, str(real_validator), str(ROOT / "evals/fixtures/invalid-real-project-report.jsonl")],
        capture_output=True, text=True,
    )
    if invalid_real.returncode == 0:
        errors.append("real-project report with changed source worktree was accepted")
    diff_selector = subprocess.run(
        [sys.executable, str(ROOT / "evals/scripts/test_select_diff_evidence.py")],
        capture_output=True, text=True,
    )
    if diff_selector.returncode:
        errors.append(f"bounded diff selector tests failed: {diff_selector.stdout}{diff_selector.stderr}")
    pr_review_safety = subprocess.run(
        [sys.executable, str(ROOT / "evals/scripts/test_pr_review_safety.py")],
        capture_output=True, text=True,
    )
    if pr_review_safety.returncode:
        errors.append(
            "PR review safety tests failed: "
            f"{pr_review_safety.stdout}{pr_review_safety.stderr}"
        )
    verification_gate = subprocess.run(
        [sys.executable, str(ROOT / "evals/scripts/test_generative_verification.py")],
        capture_output=True, text=True,
    )
    if verification_gate.returncode:
        errors.append(f"generative verification gate tests failed: {verification_gate.stdout}{verification_gate.stderr}")
    real_live_gate = subprocess.run(
        [sys.executable, str(ROOT / "evals/scripts/test_real_project_live_validation.py")],
        capture_output=True, text=True,
    )
    if real_live_gate.returncode:
        errors.append(f"real-project live gate tests failed: {real_live_gate.stdout}{real_live_gate.stderr}")
    source_listing = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    tracked_text = "\n".join(
        (ROOT / relative).read_text(encoding="utf-8", errors="ignore")
        for relative in source_listing if (ROOT / relative).is_file()
    )
    secret_patterns = (
        r"Bearer\s+[A-Za-z0-9._~+/-]{16,}",
        r"(?i)(?:api[_ -]?key|token|password)\s*[:=]\s*[A-Za-z0-9._~+/-]{24,}",
        r"\b[0-9a-fA-F]{64}\b",
    )
    if any(re.search(pattern, tracked_text) for pattern in secret_patterns):
        errors.append("possible credential material found in repository files")
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        return 1
    print(f"validated {len(REQUIRED_SKILLS)} skills, {len(behavior)} behavior cases, and {len(generative)} generative cases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
