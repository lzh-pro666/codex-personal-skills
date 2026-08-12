#!/usr/bin/env python3
"""Validate and normalize a PR evidence bundle, then collect bounded base history."""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import urllib.parse
import urllib.request


ARRAY_FILES = (
    "files.json",
    "commits.json",
    "reviews.json",
    "review_comments.json",
    "issue_comments.json",
)
CODE_SUFFIXES = {
    ".c", ".cc", ".cpp", ".cs", ".go", ".h", ".java", ".js", ".jsx",
    ".kt", ".kts", ".m", ".mm", ".php", ".py", ".rb", ".rs", ".scala",
    ".sh", ".sql", ".swift", ".ts", ".tsx",
}
REVIEW_SAMPLE_LIMIT_PER_KIND = 8
REVIEW_SUMMARY_LIMIT = 160


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def flatten_pages(payload):
    if not isinstance(payload, list):
        raise ValueError("expected a JSON array")
    if payload and all(isinstance(page, list) for page in payload):
        return [item for page in payload for item in page]
    return payload


def history_candidates(files: list[dict], limit: int = 8) -> list[str]:
    candidates = []
    for item in files:
        path = str(item.get("filename") or "")
        lowered = path.lower()
        if pathlib.PurePosixPath(path).suffix.lower() not in CODE_SUFFIXES:
            continue
        if "/generated/" in lowered or "/vendor/" in lowered or "/tests/fixtures/" in lowered:
            continue
        score = int(item.get("additions") or 0) + int(item.get("deletions") or 0)
        candidates.append((score, path))
    candidates.sort(key=lambda pair: (-pair[0], pair[1]))
    return [path for _, path in candidates[:limit]]


def fetch_history_gh(repo: str, base_sha: str, path: str) -> list[dict]:
    result = subprocess.run(
        [
            "gh",
            "api",
            "--method",
            "GET",
            f"repos/{repo}/commits",
            "-f",
            f"sha={base_sha}",
            "-f",
            f"path={path}",
            "-f",
            "per_page=20",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    if not isinstance(payload, list):
        raise ValueError("history endpoint did not return an array")
    return payload


def fetch_history_public(repo: str, base_sha: str, path: str) -> list[dict]:
    query = urllib.parse.urlencode({"sha": base_sha, "path": path, "per_page": 20})
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/commits?{query}",
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "pr-review-to-notion-skill",
        },
    )
    with urllib.request.urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("history endpoint did not return an array")
    return payload


def compact_commit(item: dict) -> dict:
    commit = item.get("commit") or {}
    author = commit.get("author") or {}
    github_author = item.get("author") or {}
    message = str(commit.get("message") or "").splitlines()[0]
    return {
        "sha": item.get("sha"),
        "date": author.get("date"),
        "author_login": github_author.get("login"),
        "author_name": author.get("name"),
        "message": message,
        "url": item.get("html_url"),
    }


def compact_summary(value, limit: int = REVIEW_SUMMARY_LIMIT) -> str:
    summary = " ".join(str(value or "").split())
    if len(summary) <= limit:
        return summary
    return summary[: limit - 1].rstrip() + "…"


def build_files_digest(files: list[dict]) -> list[dict]:
    return [
        {
            "filename": item.get("filename"),
            "status": item.get("status"),
            "additions": item.get("additions"),
            "deletions": item.get("deletions"),
            "changes": item.get("changes"),
            "previous_filename": item.get("previous_filename"),
        }
        for item in files
    ]


def build_review_digest(arrays: dict[str, list]) -> dict:
    source_names = {
        "reviews": "reviews.json",
        "review_comments": "review_comments.json",
        "issue_comments": "issue_comments.json",
    }
    samples = {}
    for kind, source_name in source_names.items():
        samples[kind] = [
            {
                "id": item.get("id"),
                "path": item.get("path"),
                "user": (item.get("user") or {}).get("login"),
                "summary": compact_summary(item.get("body")),
            }
            for item in arrays[source_name][:REVIEW_SAMPLE_LIMIT_PER_KIND]
        ]

    return {
        "counts": {
            kind: len(arrays[source_name])
            for kind, source_name in source_names.items()
        },
        "sample_limit_per_kind": REVIEW_SAMPLE_LIMIT_PER_KIND,
        "samples": samples,
    }


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_dir", type=pathlib.Path)
    parser.add_argument("--history-mode", choices=("gh", "public", "none"), required=True)
    args = parser.parse_args()
    evidence_dir = args.evidence_dir.resolve()

    pr_path = evidence_dir / "pr.json"
    diff_path = evidence_dir / "pr.diff"
    if not pr_path.is_file() or not diff_path.is_file():
        raise SystemExit("error: missing core evidence: pr.json or pr.diff")

    pr = read_json(pr_path)
    if not isinstance(pr, dict) or not pr.get("html_url") or not pr.get("title"):
        raise SystemExit("error: pr.json is not a valid GitHub PR object")
    if diff_path.stat().st_size == 0:
        raise SystemExit("error: pr.diff is empty")

    arrays: dict[str, list] = {}
    for name in ARRAY_FILES:
        path = evidence_dir / name
        try:
            normalized = flatten_pages(read_json(path))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            raise SystemExit(f"error: invalid {name}: {error}") from error
        write_json(path, normalized)
        arrays[name] = normalized

    files = arrays["files.json"]
    if not files:
        raise SystemExit("error: files.json contains no changed files")

    write_json(evidence_dir / "files_digest.json", build_files_digest(files))
    write_json(
        evidence_dir / "commits_digest.json",
        [compact_commit(item) for item in arrays["commits.json"]],
    )
    write_json(evidence_dir / "review_digest.json", build_review_digest(arrays))

    base = pr.get("base") or {}
    base_repo = (base.get("repo") or {}).get("full_name")
    base_sha = base.get("sha")
    data_gaps: list[str] = []
    history_items = []
    if args.history_mode == "none":
        data_gaps.append("path history was not collected (--history-mode none)")
    elif base_repo and base_sha:
        fetcher = fetch_history_gh if args.history_mode == "gh" else fetch_history_public
        for path in history_candidates(files):
            try:
                commits = fetcher(base_repo, base_sha, path)
                history_items.append({"path": path, "commits": [compact_commit(item) for item in commits]})
            except Exception as error:  # Optional evidence must not invalidate the core bundle.
                data_gaps.append(f"history unavailable for {path}: {error}")
    else:
        data_gaps.append("PR base repository or base SHA is missing; path history was not collected")
    write_json(evidence_dir / "history.json", history_items)

    summary = {
        "evidence_dir": str(evidence_dir),
        "pr_url": pr.get("html_url"),
        "title": pr.get("title"),
        "author": (pr.get("user") or {}).get("login"),
        "state": pr.get("state"),
        "merged": pr.get("merged"),
        "created_at": pr.get("created_at"),
        "merged_at": pr.get("merged_at"),
        "base": base.get("ref"),
        "base_sha": base_sha,
        "head": (pr.get("head") or {}).get("ref"),
        "head_sha": (pr.get("head") or {}).get("sha"),
        "files_count": len(files),
        "additions": pr.get("additions"),
        "deletions": pr.get("deletions"),
        "commits_count": len(arrays["commits.json"]),
        "reviews_count": len(arrays["reviews.json"]),
        "review_comments_count": len(arrays["review_comments.json"]),
        "issue_comments_count": len(arrays["issue_comments.json"]),
        "history_paths_count": len(history_items),
        "digest_files": ["files_digest.json", "commits_digest.json", "review_digest.json"],
        "data_gaps": data_gaps,
        "diff_sha256": sha256(diff_path),
    }
    write_json(evidence_dir / "evidence_summary.json", summary)

    manifest = {}
    mutable_outputs = {
        "evidence_manifest.json",
        "retrospective.md",
        "notion-properties.json",
        "draft_validation.json",
    }
    for path in sorted(evidence_dir.iterdir()):
        if path.is_file() and path.name not in mutable_outputs:
            manifest[path.name] = {"bytes": path.stat().st_size, "sha256": sha256(path)}
    write_json(evidence_dir / "evidence_manifest.json", {"files": manifest})
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
