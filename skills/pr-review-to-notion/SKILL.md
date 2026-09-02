---
name: pr-review-to-notion
description: Analyze exactly one GitHub pull request from its URL, create an evidence-first Chinese engineering retrospective, and optionally archive it in a configured Notion data source. Use for PR 总结、复盘、学习或 Notion 归档; support validated draft-only output.
---

# PR Review to Notion

Analyze one PR without modifying GitHub or the repository. Keep facts, inferences, and recommendations distinct; report a Notion write only after read-back verification.

## Evidence workflow

1. Run `scripts/fetch_pr_evidence.sh <PR_URL>` from this skill's repository root and use the returned fresh `evidence_dir`; reuse a bundle only for explicitly offline work.
2. Verify `evidence_manifest.json`, then read `evidence_summary.json` and `files_digest.json`. Stop if metadata, changed files, or diff integrity fails.
3. Read `pr.diff` only when small. For larger changes, use `scripts/select_diff_evidence.py` for decision-relevant paths and retain truncation as a data gap. Use bounded commit/review/history digests for orientation; load exact review entries only through `scripts/select_review_evidence.py`.
4. Treat the PR diff as authority. Do not use the current worktree or an index built at another revision as historical evidence.
5. Write `retrospective.md` and `notion-properties.json` in the evidence directory, then run `scripts/validate_draft.py`. Redact every reported credential/PII match with its placeholder and rerun before any external write.
6. For draft-only work, return the validated files, conclusion, and data gaps. For a requested Notion write, read `references/notion-schema.md`, resolve the ignored local target, verify the live schema, and search the canonical PR URL. Ask before creating a duplicate.
7. Create at most one page, write the complete body/properties, and read it back. Report its URL only after the PR URL, title, and first required heading match.

## Retrospective contract

Use these `##` headings once and in order:

1. `证据与数据缺口`
2. `PR 类型与一句话结论`
3. `这个 PR 改变了什么`
4. `关键实现与取舍`
5. `改造前后对比`
6. `风险、遗漏与建议`
7. `我能学到什么`

Add code, review, bot, or history sections only when supported. Prefer behavior, state/data flow, lifecycle/async/persistence, compatibility, meaningful review feedback, risk, and reusable lessons over file narration or generated churn. Include one to three exact snippets only for meaningful source changes.

## Boundaries

- Label material ambiguity as `事实`, `推断`, or `建议`; treat bot output as third-party evidence and record missing optional evidence under `数据缺口`.
- Use path history as context, never proof of ownership or authorship. Never infer truncated review content.
- Do not write Notion after failed evidence, draft, schema, or duplicate checks. After a partial write, report the existing page and failed step; do not create another page automatically.
- Evaluation or dry-run work may create local drafts and perform read-only schema/deduplication checks, but never mutate production Notion.
- Keep single-PR archives in Notion and reusable cross-PR knowledge in Obsidian; cross-link by canonical PR URL instead of copying the full retrospective.
