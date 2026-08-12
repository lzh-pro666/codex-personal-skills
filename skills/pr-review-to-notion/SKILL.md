---
name: pr-review-to-notion
description: Analyze exactly one GitHub pull request from its URL, create an evidence-first Chinese engineering retrospective, and optionally archive it in a locally configured Notion data source. Use for PR 总结、复盘、学习或 Notion 归档; support validated draft-only output when Notion is unavailable or writing is not requested.
---

# PR Review to Notion

Analyze one PR without modifying GitHub or the repository. Keep facts, inferences, and recommendations distinct, and never report a Notion write before read-back verification.

## Workflow

1. Run `scripts/fetch_pr_evidence.sh <PR_URL>` from the repository root and use the new `evidence_dir`. Reuse a bundle only for an explicitly offline task.
2. Read `evidence_summary.json` and verify `evidence_manifest.json`. Stop if PR metadata, changed files, or the diff is invalid.
3. Use `files_digest.json` to size and rank the change. For a small diff, read `pr.diff`; for a large diff, select only decision-relevant paths with `scripts/select_diff_evidence.py` and keep the reported truncation as a data gap. Use `commits_digest.json`, `review_digest.json`, and `history.json` for orientation. `review_digest.json` contains counts plus at most eight `id`/`path`/`user`/short-summary samples per review kind; compare sample lengths with counts. Load complete review text only through `scripts/select_review_evidence.py` with an ID, path, user, or search term; never print a raw review array wholesale.
4. Treat the PR diff as authoritative. Do not use the current worktree or GitNexus as historical evidence unless checked out or indexed at the PR base/head commit.
5. Write `retrospective.md` and `notion-properties.json` in the evidence directory, then run `python3 scripts/validate_draft.py <evidence_dir>`. The validator scans both files for high-confidence credentials and obvious email/phone PII. Redact every finding with the reported placeholder and rerun it before any external write; ordinary unlabeled Git SHAs and checksums are allowed.
6. For draft-only work, return the validated files, data gaps, and conclusion without loading the Notion reference.
7. For a Notion write, read `references/notion-schema.md`, resolve the ignored local target configuration, verify the live schema, and search the exact canonical PR URL. If a page exists, ask whether to update it or create a duplicate.
8. Create at most one page, write the complete body and all properties, then read it back. Report the page URL only after confirming the PR URL, title, and first required heading.

## Evidence Guardrails

- Label material ambiguity as `事实`, `推断`, or `建议`.
- Attribute bot output as third-party evidence. Ignore billing, rate-limit, status, and generated boilerplate unless it changed the review outcome.
- Use path history only as change context, never as ownership or function-authorship proof.
- Record missing optional evidence under `数据缺口`; do not fill gaps from memory.
- Prioritize runtime/user behavior, state and data flow, lifecycle/async/persistence, compatibility, meaningful review feedback, risk, and reusable lessons.
- Deprioritize generated files, repeated localization rows, formatting, lockfiles, and file-by-file narration.
- Include one to three exact diff snippets only for meaningful source changes. Omit snippets for docs/config-only changes.

## Retrospective Contract

Use these required `##` headings once and in this order:

1. `证据与数据缺口`
2. `PR 类型与一句话结论`
3. `这个 PR 改变了什么`
4. `关键实现与取舍`
5. `改造前后对比`
6. `风险、遗漏与建议`
7. `我能学到什么`

Add `关键代码片段与解析`, `Review 反馈与处理`, `机器人提出的可执行问题`, or `相关路径的历史改动背景` only when supported by evidence. Do not add empty headings or repeat the same summary.

## Failure Boundaries

- Do not write Notion when evidence, draft validation, schema validation, or duplicate checks fail.
- Treat a sensitive-content finding as a failed draft validation. Never copy the matched value into logs, chat, or a Notion page.
- In an evaluation, dry run, or Skill test, allow local drafts plus read-only schema and duplicate queries only. Never create or update a production Notion page.
- After a partial write, report the existing page and failed step; never create a second page as an automatic retry.
- Do not edit the PR, comments, labels, reviewers, branches, or repository files.
- If Notion is unavailable, keep the validated local draft and report only the blocked external write.

## Knowledge-layer boundary

Use Notion for a single-PR evidence archive and personal retrospective. Use Obsidian for reusable technical knowledge that survives beyond one PR. Cross-link them by the canonical PR URL; do not copy the complete retrospective into a developer note.

## Resources

- `scripts/fetch_pr_evidence.sh`: fetch one fresh PR bundle.
- `scripts/build_evidence_index.py`: normalize pagination, validate evidence, generate bounded digests, and collect bounded pre-PR path history.
- `scripts/select_review_evidence.py`: return bounded exact review entries without loading whole raw arrays into model context.
- `scripts/select_diff_evidence.py`: return bounded unified-diff sections for exact paths selected from `files_digest.json`.
- `scripts/validate_draft.py`: verify evidence integrity, properties, limits, PR identity, and retrospective structure.
- `references/notion-schema.md`: load only for Notion preflight, property mapping, write, and read-back.
