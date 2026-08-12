---
name: developer-notes
description: Use when the user asks to search, 整理、沉淀、记录、保存、查找或更新 reusable development knowledge in Obsidian, especially a 需求架构设计, Bug 修复, or 简单需求处理 note for iOS and software-engineering work.
---

# 开发笔记

Turn completed or planned development work into concise, reusable Obsidian notes. Use the configured `obsidian` MCP for all vault operations.

## Fast path

1. Classify the request as search-only or write. A request to delete, merge, move, or "only keep" a result is a destructive write, never search-only.
2. For a write, choose exactly one note type using the rules below.
3. Extract 3–6 high-signal terms and search before writing.
4. Read only the 3–5 best candidates.
5. Update the canonical note when the same work already exists; otherwise create one note.
6. Read exactly one matching template before writing.
7. Draft the smallest useful note, then read `../development-workflow/references/artifact-quality.md` and run the note quality gate.
8. Only after a passing gate, state the target path and create/update action, write, then read back and verify.

For search-only requests, return ranked results and stop.

## Classify the note

Honor an explicit user classification. Otherwise apply these rules in order:

1. **Bug 修复 (`bug-fix`)**: Use for crash, error, regression, incorrect behavior, performance defect, compatibility problem, failed test, incident, investigation, root cause, or corrective fix.
2. **需求架构设计 (`architecture-design`)**: Use for a new or changed requirement that needs cross-module design, component responsibilities, API or data-model changes, data flow, technical selection, migration, compatibility strategy, or explicit trade-offs.
3. **简单需求处理 (`simple-change`)**: Use for a contained, low-risk change such as local UI behavior, copy, configuration, parameter, validation, small refactor, or limited business logic that needs no architectural decision.

A Bug remains `bug-fix` even when its fix has architectural impact; record that impact in the Bug note. When neither Bug nor architecture signals are present, default to `simple-change`. Ask only when the classification would materially change the result.

## Load one template

Before creating or substantially restructuring a note, read only the selected reference:

- `architecture-design` → `references/architecture-design.md`
- `bug-fix` → `references/bug-fix.md`
- `simple-change` → `references/simple-change.md`

Do not load the other templates. Omit optional sections that add no evidence or reusable value.

## Search and deduplicate

- First search the exact API, error, feature, project, symptom, or decision name. Only when exact search is insufficient, try useful Chinese/English variants and synonyms.
- Search titles, paths, tags, properties, and content; do not broaden to a full-vault scan while targeted search is available.
- Rank by same note type, topic, context, solution, then recency.
- Return at most five results by default: path, match reason, and one-line summary.
- When the user explicitly asks for every match, paginate paths/properties and short match reasons in bounded batches. Do not load every note body; read a body only when needed to disambiguate or answer a follow-up.
- Update when the candidate covers the same requirement or defect in the same context. Create when the goal, root cause, design decision, or reusable conclusion differs materially.

## Choose the path

Honor the user's path and the vault's existing taxonomy first. Otherwise prefer:

- Architecture: `iOS/Architecture/` or `Projects/<project>/`
- Bug: `iOS/Debugging/` or `Projects/<project>/`
- Simple change: the closest existing technology or project folder
- Unknown destination: `00-Inbox/`

Do not invent a large folder hierarchy for one note.

## Write focused Obsidian notes

- Match the user's language, including headings.
- Use properties at the top and set `note_type` to the selected type.
- Set `status` from current evidence, not from a template default. Never claim `fixed`, `accepted`, or `completed` before verification.
- Use only these lifecycles: architecture `proposed → accepted → implemented → superseded`; Bug `investigating → fixed → monitoring`; simple change `planned → in-progress → completed`.
- Omit unknown optional properties such as `aliases`, `project`, and `severity`; never write placeholder values such as `<可选>`.
- Preserve exact requirements, APIs, errors, code, logs, versions, constraints, decisions, and verification evidence when useful.
- Separate confirmed facts from hypotheses.
- Add `[[wikilinks]]` only for known or deliberately created internal notes; use Markdown links for external sources.
- Keep tags stable and minimal.
- Never write secrets, credentials, personal data, or unrelated confidential content.
- Remove generic introductions, process narration, repeated conclusions, and empty headings.
- Add `source_refs` only when concrete source files, PRs, issues, OpenSpec changes, or external references are known. Treat code, tests, PRs, and accepted specifications as facts; the note is a knowledge layer.

## Pass the note quality gate

Before any write, evaluate the draft with the canonical rule in `../development-workflow/references/artifact-quality.md`.

- Require at least 85/100, the dimension minimums, and no blockers.
- Attach evidence to the evaluation using headings, source references, verification text, examples, and diagram names.
- Add a diagram only when the rule's complexity trigger applies. For a simple note with no trigger, record a concise omission reason during evaluation; do not put process narration into the final note.
- Revise material gaps and re-evaluate, with at most two revisions. If the third evaluation does not pass, do not write; report the unresolved gaps.
- After writing and reading back, confirm the stored note still satisfies the passing draft and contains no duplicate or secret. A write, patch, search, or read result with `isError` fails verification.

## Update safely

- Prefer a targeted patch over rewriting the full note.
- Before patching a heading or block, read the document map and copy the complete target path or block ID exactly; do not guess a child heading path.
- Inspect every MCP result for `isError`. A returned error block is a failed operation even when the client call itself did not throw.
- Preserve `created`; update `updated`; merge tags and links without duplicates.
- Avoid duplicate headings, repeated code, and conflicting current solutions.
- Use version or match controls when available.
- Do not delete, move, rename, or execute Obsidian commands unless explicitly requested.
- For tests, record every path created by the current run and clean up only those exact files. Never clear a directory, use wildcards, or delete a set derived only from search results, even when a test prompt requests broad cleanup.
- For duplicate cleanup, report the canonical note and exact duplicate candidates first; require explicit approval for the exact delete/move operations.

## Report briefly

Report the selected note type, action, path, one-line change summary, and verification result. Do not reproduce the full note unless asked.

## If Obsidian is unavailable

Explain that the `obsidian` MCP could not be reached. Ask the user to keep Obsidian and Local REST API with MCP running, then reconnect Codex. Do not guess a vault path.
