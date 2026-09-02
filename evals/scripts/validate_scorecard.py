#!/usr/bin/env python3
"""Validate artifact-quality scorecards without pretending to judge semantics."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys


SPECS = {
    "code": {
        "dimensions": {
            "functional_correctness": (30, 24),
            "architecture_maintainability": (20, 0),
            "tests_verification": (20, 16),
            "robustness_security": (15, 0),
            "readability_naming": (10, 0),
            "scope_control": (5, 0),
        },
    },
    "note": {
        "dimensions": {
            "understandability": (25, 20),
            "completeness": (25, 20),
            "correctness_evidence": (20, 16),
            "searchability_traceability": (10, 0),
            "structure_concision": (10, 0),
            "diagrams_examples": (10, 0),
        },
    },
    "workflow": {
        "dimensions": {
            "classification_routing": (15, 12),
            "requirements_alignment": (15, 12),
            "implementation_scope": (15, 0),
            "verification_strategy": (20, 16),
            "evidence_integrity": (15, 12),
            "context_efficiency": (10, 8),
            "handoff_capture": (10, 0),
        },
    },
}
REQUIRED_KEYS = {"run_id", "case_id", "attempt", "artifact_type", "dimensions", "blockers", "total", "decision"}
SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.IGNORECASE),
    re.compile(r"(?i)(?:api[_ -]?key|token|password)\s*[:=]\s*[A-Za-z0-9._~+/-]{16,}"),
)


def load_scorecards(path: pathlib.Path) -> list[dict]:
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else [payload]


def is_nonempty_strings(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def contains_secret(payload: dict) -> bool:
    serialized = json.dumps(payload, ensure_ascii=False)
    return any(pattern.search(serialized) for pattern in SECRET_PATTERNS)


def validate(card: dict, source: str) -> list[str]:
    errors: list[str] = []
    prefix = f"{source}:{card.get('case_id', '<unknown>')}"
    if set(card) != REQUIRED_KEYS:
        errors.append(f"{prefix}: keys must be exactly {sorted(REQUIRED_KEYS)}")
        return errors
    artifact_type = card.get("artifact_type")
    if artifact_type not in SPECS:
        return [f"{prefix}: unsupported artifact_type: {artifact_type}"]
    if not isinstance(card.get("case_id"), str) or not card["case_id"].strip():
        errors.append(f"{prefix}: case_id must be a non-empty string")
    if not isinstance(card.get("run_id"), str) or not card["run_id"].strip():
        errors.append(f"{prefix}: run_id must be a non-empty string")
    if card.get("attempt") not in {1, 2, 3}:
        errors.append(f"{prefix}: attempt must be 1, 2, or 3")
    if card.get("decision") not in {"pass", "revise", "fail"}:
        errors.append(f"{prefix}: invalid decision")
    if not is_nonempty_strings(card.get("blockers")) and card.get("blockers") != []:
        errors.append(f"{prefix}: blockers must be a list of non-empty strings")
    dimensions = card.get("dimensions")
    if not isinstance(dimensions, list):
        return errors + [f"{prefix}: dimensions must be an array"]
    expected = SPECS[artifact_type]["dimensions"]
    actual: dict[str, dict] = {}
    for dimension in dimensions:
        if not isinstance(dimension, dict) or set(dimension) != {"name", "score", "max_score", "evidence", "gaps"}:
            errors.append(f"{prefix}: invalid dimension shape")
            continue
        name = dimension.get("name")
        if not isinstance(name, str) or name in actual:
            errors.append(f"{prefix}: dimension names must be unique strings")
            continue
        actual[name] = dimension
        if not is_nonempty_strings(dimension.get("evidence")):
            errors.append(f"{prefix}:{name}: evidence must contain observed references")
        if not is_nonempty_strings(dimension.get("gaps")) and dimension.get("gaps") != []:
            errors.append(f"{prefix}:{name}: gaps must be a list of non-empty strings")
    if set(actual) != set(expected):
        errors.append(f"{prefix}: dimensions must be exactly {sorted(expected)}")
        return errors
    computed_total = 0
    minimums_pass = True
    for name, (maximum, minimum) in expected.items():
        dimension = actual[name]
        score = dimension.get("score")
        if dimension.get("max_score") != maximum:
            errors.append(f"{prefix}:{name}: max_score must be {maximum}")
        if not isinstance(score, int) or isinstance(score, bool) or not 0 <= score <= maximum:
            errors.append(f"{prefix}:{name}: score must be an integer from 0 to {maximum}")
            continue
        computed_total += score
        minimums_pass = minimums_pass and score >= minimum
    if card.get("total") != computed_total:
        errors.append(f"{prefix}: total {card.get('total')} does not equal {computed_total}")
    qualifies = computed_total >= 85 and minimums_pass and not card.get("blockers")
    if (card.get("decision") == "pass") != qualifies:
        errors.append(f"{prefix}: decision must be {'pass' if qualifies else 'revise or fail'}")
    if card.get("attempt") == 3 and card.get("decision") == "revise":
        errors.append(f"{prefix}: attempt 3 must be pass or fail")
    if contains_secret(card):
        errors.append(f"{prefix}: possible secret or credential in scorecard")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=pathlib.Path)
    parser.add_argument("--suite", action="store_true", help="require all pass and average >= 90")
    args = parser.parse_args()
    all_cards: list[dict] = []
    errors: list[str] = []
    for path in args.paths:
        try:
            cards = load_scorecards(path)
        except (OSError, json.JSONDecodeError) as error:
            errors.append(f"{path}: cannot load scorecard: {error}")
            continue
        all_cards.extend(cards)
        for card in cards:
            if not isinstance(card, dict):
                errors.append(f"{path}: scorecard must be an object")
            else:
                errors.extend(validate(card, str(path)))
    if args.suite:
        if not all_cards:
            errors.append("suite: at least one scorecard is required")
        latest_cards: list[dict] = []
        revision_groups: dict[tuple[str, str], list[dict]] = {}
        for card in all_cards:
            if isinstance(card, dict):
                revision_groups.setdefault((card.get("run_id"), card.get("case_id")), []).append(card)
        for (run_id, case_id), cards in revision_groups.items():
            attempts = sorted(card.get("attempt") for card in cards)
            if attempts != list(range(1, len(attempts) + 1)) or len(attempts) > 3:
                errors.append(f"suite:{run_id}:{case_id}: attempts must be contiguous from 1 to at most 3")
            ordered = sorted(cards, key=lambda card: card.get("attempt", 0))
            if any(card.get("decision") == "pass" for card in ordered[:-1]):
                errors.append(f"suite:{run_id}:{case_id}: no attempt may follow a passing result")
            latest_cards.append(ordered[-1])
        by_type: dict[str, list[dict]] = {}
        for card in latest_cards:
            by_type.setdefault(card.get("artifact_type"), []).append(card)
        for artifact_type, cards in by_type.items():
            average = sum(card.get("total", 0) for card in cards) / len(cards)
            if average < 90:
                errors.append(f"suite:{artifact_type}: average {average:.2f} is below 90")
            if any(card.get("decision") != "pass" for card in cards):
                errors.append(f"suite:{artifact_type}: every latest scorecard must pass")
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors), file=sys.stderr)
        return 1
    average = sum(card["total"] for card in all_cards) / len(all_cards) if all_cards else 0
    print(f"validated {len(all_cards)} scorecard(s); average={average:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
