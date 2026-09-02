#!/usr/bin/env python3
"""Evaluate the Siuper Android Skill package, routing cases, and installation."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import subprocess


ROOT = pathlib.Path(__file__).resolve().parents[2]
PROJECT_SKILL = ROOT / "skills/android-kotlin-mvvm"
BEHAVIOR_CASES = ROOT / "evals/cases/behavior-cases.jsonl"
OFFICIAL_SKILLS = {
    "edge-to-edge": "system bars and IME insets",
    "android-intent-security": "Intent and component security",
    "r8-analyzer": "R8 and Proguard analysis",
}


def load_jsonl(path: pathlib.Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def frontmatter_name(path: pathlib.Path) -> str | None:
    if not path.is_file():
        return None
    match = re.match(r"---\n.*?^name:\s*([^\n]+)", path.read_text(encoding="utf-8"), re.DOTALL | re.MULTILINE)
    return match.group(1).strip() if match else None


def rg_evidence(project: pathlib.Path, pattern: str) -> list[str]:
    result = subprocess.run(
        [
            "rg", "--files-with-matches", "--glob", "*.kt", "--glob", "*.kts",
            "--glob", "*.toml", "--glob", "!**/build/**", pattern, str(project),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode not in {0, 1}:
        raise RuntimeError(result.stderr.strip() or f"rg failed for {pattern}")
    return [
        str(pathlib.Path(line).relative_to(project))
        for line in result.stdout.splitlines()[:3]
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=pathlib.Path, default=pathlib.Path("/Users/admin/project/siuper-sdk-android"))
    parser.add_argument("--skills-dir", type=pathlib.Path, default=pathlib.Path.home() / ".agents/skills")
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()

    checks: list[dict] = []

    def record(name: str, passed: bool, evidence: list[str]) -> None:
        checks.append({"name": name, "passed": passed, "evidence": evidence})

    project_skill_name = frontmatter_name(PROJECT_SKILL / "SKILL.md")
    record(
        "project_skill_package",
        project_skill_name == "android-kotlin-mvvm" and (PROJECT_SKILL / "agents/openai.yaml").is_file(),
        [f"frontmatter={project_skill_name}", "agents/openai.yaml"],
    )

    skill_entry = PROJECT_SKILL / "SKILL.md"
    convention_reference = PROJECT_SKILL / "references/siuper-android-conventions.md"
    reference_linked = (
        convention_reference.is_file()
        and "references/siuper-android-conventions.md" in skill_entry.read_text(encoding="utf-8")
    )
    record(
        "project_reference_routing",
        reference_linked,
        ["references/siuper-android-conventions.md", f"linked={reference_linked}"],
    )

    installed = []
    invalid = []
    for name, purpose in OFFICIAL_SKILLS.items():
        actual = frontmatter_name(args.skills_dir / name / "SKILL.md")
        if actual == name:
            installed.append(f"{name}: {purpose}")
        else:
            invalid.append(f"{name}: frontmatter={actual}")
    record("official_skill_installation", not invalid, installed + invalid)

    cases = [case for case in load_jsonl(BEHAVIOR_CASES) if case.get("category") == "android_routing"]
    case_ids = {case.get("id") for case in cases}
    route_coverage = {
        skill
        for case in cases
        for skill in case.get("expected", {}).get("skills", [])
    }
    expected_routes = {"android-kotlin-mvvm", *OFFICIAL_SKILLS}
    routing_ok = (
        bool(cases)
        and len(case_ids) == len(cases)
        and expected_routes.issubset(route_coverage)
        and all("android-kotlin-mvvm" in case["expected"]["skills"] for case in cases)
    )
    record(
        "android_behavior_routing",
        routing_ok,
        [f"cases={len(cases)}", f"routes={','.join(sorted(route_coverage))}"],
    )

    project_files = ["AGENTS.md", "settings.gradle.kts", "gradle/libs.versions.toml"]
    missing_project_files = [relative for relative in project_files if not (args.project / relative).is_file()]
    record(
        "project_entry_evidence",
        not missing_project_files,
        [f"project={args.project}"] + [f"missing={item}" for item in missing_project_files],
    )

    evidence_patterns = {
        "BaseViewModel": r"class\s+BaseViewModel|BaseViewModel<",
        "manager boundary": r"SiuperManager|I[A-Za-z]+Manager",
        "hybrid UI": r"ComposeView|AndroidView\(",
        "coroutine testing": r"MainDispatcherRule|StandardTestDispatcher|runTest\(",
        "Robolectric": r"robolectric",
    }
    missing_patterns = []
    observed = []
    if args.project.is_dir():
        for label, pattern in evidence_patterns.items():
            matches = rg_evidence(args.project, pattern)
            if matches:
                observed.append(f"{label}={matches[0]}")
            else:
                missing_patterns.append(label)
    else:
        missing_patterns.extend(evidence_patterns)
    record("project_claim_evidence", not missing_patterns, observed + [f"missing={item}" for item in missing_patterns])

    passed_count = sum(check["passed"] for check in checks)
    report = {
        "suite": "siuper-android-skill",
        "score": round(passed_count / len(checks) * 100),
        "passed": passed_count == len(checks),
        "checks": checks,
        "build_executed": False,
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
