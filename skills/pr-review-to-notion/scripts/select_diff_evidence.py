#!/usr/bin/env python3
"""Select bounded file sections from a Git unified diff."""

from __future__ import annotations

import argparse
import json
import pathlib
import shlex


def split_files(diff: str) -> list[tuple[str, list[str]]]:
    sections: list[tuple[str, list[str]]] = []
    path: str | None = None
    lines: list[str] = []
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            if path is not None:
                sections.append((path, lines))
            tokens = shlex.split(line)
            if len(tokens) != 4 or not tokens[3].startswith("b/"):
                raise ValueError("invalid diff header")
            path = tokens[3][2:]
            lines = [line]
        elif path is not None:
            lines.append(line)
    if path is not None:
        sections.append((path, lines))
    return sections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=pathlib.Path)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--max-lines", type=int, default=1200)
    args = parser.parse_args()

    if not args.path:
        raise SystemExit("error: provide at least one --path selector")
    if not 1 <= args.max_lines <= 5000:
        raise SystemExit("error: --max-lines must be between 1 and 5000")

    try:
        sections = split_files((args.evidence_dir / "pr.diff").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        raise SystemExit(f"error: invalid pr.diff: {error}") from error

    selected = [(path, lines) for path, lines in sections if path in set(args.path)]
    missing = sorted(set(args.path) - {path for path, _ in selected})
    if missing:
        raise SystemExit(f"error: path not found in pr.diff: {', '.join(missing)}")

    all_lines = [line for _, lines in selected for line in lines]
    bounded = all_lines[: args.max_lines]
    print(json.dumps({
        "files": [path for path, _ in selected],
        "truncated": len(bounded) < len(all_lines),
        "original_lines": len(all_lines),
        "returned_lines": len(bounded),
        "diff": "\n".join(bounded) + ("\n" if bounded else ""),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
