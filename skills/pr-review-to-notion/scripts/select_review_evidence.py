#!/usr/bin/env python3
"""Select bounded review evidence from large raw GitHub arrays."""

from __future__ import annotations

import argparse
import json
import pathlib


SOURCES = {
    "reviews": "reviews.json",
    "review-comments": "review_comments.json",
    "issue-comments": "issue_comments.json",
}


def read_array(path: pathlib.Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"expected array: {path.name}")
    return payload


def user_login(item: dict) -> str:
    return str((item.get("user") or {}).get("login") or "")


def matches(item: dict, args: argparse.Namespace) -> bool:
    if args.ids and str(item.get("id")) not in args.ids:
        return False
    if args.path and args.path.casefold() not in str(item.get("path") or "").casefold():
        return False
    if args.user and args.user.casefold() not in user_login(item).casefold():
        return False
    if args.search:
        haystack = "\n".join(
            (
                str(item.get("body") or ""),
                str(item.get("path") or ""),
                user_login(item),
            )
        ).casefold()
        if args.search.casefold() not in haystack:
            return False
    return True


def bounded_body(value, limit: int) -> tuple[str, bool, int]:
    body = str(value or "")
    if len(body) <= limit:
        return body, False, len(body)
    return body[:limit] + "\n…[truncated by selector]", True, len(body)


def compact(kind: str, item: dict, body_limit: int) -> dict:
    body, truncated, original_chars = bounded_body(item.get("body"), body_limit)
    return {
        "kind": kind,
        "id": item.get("id"),
        "in_reply_to_id": item.get("in_reply_to_id"),
        "pull_request_review_id": item.get("pull_request_review_id"),
        "user": user_login(item),
        "user_type": (item.get("user") or {}).get("type"),
        "state": item.get("state"),
        "path": item.get("path"),
        "line": item.get("line"),
        "start_line": item.get("start_line"),
        "created_at": item.get("created_at") or item.get("submitted_at"),
        "commit_id": item.get("commit_id"),
        "body": body,
        "body_truncated": truncated,
        "body_original_chars": original_chars,
        "html_url": item.get("html_url"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=pathlib.Path)
    parser.add_argument("--kind", choices=(*SOURCES, "all"), default="all")
    parser.add_argument("--id", dest="ids", action="append", default=[])
    parser.add_argument("--path")
    parser.add_argument("--user")
    parser.add_argument("--search")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--body-limit", type=int, default=3000)
    args = parser.parse_args()

    if not (args.ids or args.path or args.user or args.search):
        raise SystemExit("error: provide at least one --id, --path, --user, or --search selector")
    if args.limit < 1 or args.limit > 100:
        raise SystemExit("error: --limit must be between 1 and 100")
    if args.body_limit < 200 or args.body_limit > 20000:
        raise SystemExit("error: --body-limit must be between 200 and 20000")

    evidence_dir = args.evidence_dir.resolve()
    kinds = SOURCES if args.kind == "all" else {args.kind: SOURCES[args.kind]}
    results = []
    for kind, filename in kinds.items():
        try:
            items = read_array(evidence_dir / filename)
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise SystemExit(f"error: invalid {filename}: {error}") from error
        for item in items:
            if matches(item, args):
                results.append(compact(kind, item, args.body_limit))
                if len(results) >= args.limit:
                    break
        if len(results) >= args.limit:
            break

    print(json.dumps({"count": len(results), "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
