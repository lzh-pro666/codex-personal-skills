#!/usr/bin/env bash
# Fetch evidence for exactly one GitHub PR URL into an ignored local artifact directory.

set -euo pipefail

die() {
  echo "error: $*" >&2
  exit 1
}

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"
}

need_cmd python3
need_cmd curl

pr_url="${1:-}"
[[ -n "$pr_url" ]] || die "usage: $0 <https://github.com/OWNER/REPO/pull/NUMBER>"

parsed="$(python3 - "$pr_url" <<'PY'
import re
import sys

url = sys.argv[1].strip()
match = re.fullmatch(
    r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)(?:/(?:files|changes))?/?(?:\?.*)?",
    url,
)
if match:
    print(" ".join(match.groups()))
PY
)"
[[ -n "$parsed" ]] || die "invalid GitHub PR URL: $pr_url"

read -r owner repo number <<<"$parsed"

use_gh=0
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
  use_gh=1
fi

timestamp="$(date -u +"%Y%m%dT%H%M%SZ")"
out_root="${PR_REVIEW_OUTPUT_ROOT:-.codex-artifacts/pr-review}"
mkdir -p "$out_root"
out_dir="$(mktemp -d "${out_root}/${owner}-${repo}-pr${number}-${timestamp}-XXXXXX")"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Writing evidence to: $out_dir" >&2
if [[ "$use_gh" == "1" ]]; then
  echo "Fetch mode: gh api (authenticated)" >&2
else
  echo "Fetch mode: public GitHub API fallback (unauthenticated)" >&2
fi

pr_api="repos/${owner}/${repo}/pulls/${number}"

if [[ "$use_gh" == "1" ]]; then
  gh api "$pr_api" >"${out_dir}/pr.json"
  # --slurp preserves page boundaries; build_evidence_index.py flattens them.
  gh api "${pr_api}/files?per_page=100" --paginate --slurp >"${out_dir}/files.json"
  gh api "${pr_api}/commits?per_page=100" --paginate --slurp >"${out_dir}/commits.json"
  gh api "${pr_api}/reviews?per_page=100" --paginate --slurp >"${out_dir}/reviews.json"
  gh api "${pr_api}/comments?per_page=100" --paginate --slurp >"${out_dir}/review_comments.json"
  gh api "repos/${owner}/${repo}/issues/${number}/comments?per_page=100" --paginate --slurp >"${out_dir}/issue_comments.json"
  gh api "$pr_api" -H "Accept: application/vnd.github.v3.diff" >"${out_dir}/pr.diff"
else
  python3 - "$out_dir" "$owner" "$repo" "$number" <<'PY'
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

out_dir = pathlib.Path(sys.argv[1])
owner, repo, number = sys.argv[2:5]
headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "pr-review-to-notion-skill",
}


def request_json(url: str):
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8")), response.headers.get("Link", "")


def next_url(link_header: str):
    for part in link_header.split(","):
        if 'rel="next"' in part:
            match = re.search(r"<([^>]+)>", part)
            return match.group(1) if match else None
    return None


def fetch_object(endpoint: str):
    payload, _ = request_json(f"https://api.github.com/{endpoint}")
    if not isinstance(payload, dict):
        raise ValueError(f"expected object: {endpoint}")
    return payload


def fetch_array(endpoint: str):
    url = f"https://api.github.com/{endpoint}?per_page=100"
    items = []
    while url:
        payload, link = request_json(url)
        if not isinstance(payload, list):
            raise ValueError(f"expected array: {endpoint}")
        items.extend(payload)
        url = next_url(link)
    return items


def write(name: str, payload):
    (out_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


try:
    write("pr.json", fetch_object(f"repos/{owner}/{repo}/pulls/{number}"))
    write("files.json", fetch_array(f"repos/{owner}/{repo}/pulls/{number}/files"))
    write("commits.json", fetch_array(f"repos/{owner}/{repo}/pulls/{number}/commits"))
    write("reviews.json", fetch_array(f"repos/{owner}/{repo}/pulls/{number}/reviews"))
    write("review_comments.json", fetch_array(f"repos/{owner}/{repo}/pulls/{number}/comments"))
    write("issue_comments.json", fetch_array(f"repos/{owner}/{repo}/issues/{number}/comments"))
except urllib.error.HTTPError as error:
    detail = error.read().decode("utf-8", errors="replace")
    raise SystemExit(f"GitHub API failed ({error.code}): {detail}") from error
PY
  curl -fsSL \
    -H "Accept: application/vnd.github.v3.diff" \
    -H "User-Agent: pr-review-to-notion-skill" \
    "https://api.github.com/repos/${owner}/${repo}/pulls/${number}" >"${out_dir}/pr.diff"
fi

mode="public"
[[ "$use_gh" == "1" ]] && mode="gh"
python3 "${script_dir}/build_evidence_index.py" "$out_dir" --history-mode "$mode"
