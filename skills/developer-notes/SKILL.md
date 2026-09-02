---
name: developer-notes
description: Use when the user asks to search, 整理、沉淀、记录、保存、查找或更新 reusable software-engineering or technical-learning knowledge in Obsidian, including learning, architecture, Bug, and simple-change notes. Do not use for Word/PDF deliverables or single-PR retrospectives.
---

# 开发笔记

Search or maintain concise, reusable Obsidian knowledge through the configured `obsidian` MCP. Preserve source authority: repository artifacts and observed verification are facts; notes are derived knowledge.

## Workflow

1. Decide whether the request is search-only or a write. Delete, merge, move, rename, and “only keep” are destructive writes.
2. For a write, select one note type, run targeted deduplication, and read only the matching template.
3. Draft the smallest useful note from available evidence and apply the routed quality gate in `../development-workflow/references/artifact-quality.md`.
4. Create or patch one canonical note only after the draft passes. Read it back and verify content, properties, duplicates, and MCP errors.

Search-only requests return ranked paths, match reasons, and short summaries, then stop.

## Note types and templates

Honor the user's classification; otherwise use the first matching type:

| Type | Use when | Template |
| --- | --- | --- |
| `bug-fix` | Crash, regression, incorrect behavior, performance or compatibility defect, failed test, incident, investigation, or corrective fix | `references/bug-fix.md` |
| `architecture-design` | A requirement needs cross-module design, API/data changes, migration, compatibility, or material trade-offs | `references/architecture-design.md` |
| `learning-note` | The goal is understanding a concept, source, framework, experiment, or reusable technique rather than recording a project change | `references/learning-note.md` |
| `simple-change` | A contained project change has clear behavior and no architectural decision | `references/simple-change.md` |

A Bug remains `bug-fix` even if its fix affects architecture. Read no other template unless the classification changes.

## Search, deduplicate, and place

- Search exact APIs, errors, features, projects, symptoms, decisions, source titles, and common aliases before broadening. Read only the best candidates needed to distinguish them; return at most five results by default.
- Update when goal/context and root cause, design decision, or reusable conclusion match. Create when they differ materially. Do not merge source, concept, and practice learning notes merely because they share a topic.
- Honor the requested path and existing vault taxonomy. Otherwise use the closest existing project, technology, learning, architecture, or debugging folder; fall back to `00-Inbox/` without inventing a hierarchy.

## Content and evidence

- Match the user's language. Set `note_type` and an evidence-supported `status`; omit unknown optional properties and placeholder values.
- Lifecycles: architecture `proposed → accepted → implemented → superseded`; Bug `investigating → fixed → monitoring`; learning `captured → understood → practiced → verified` (or `outdated`); simple change `planned → in-progress → completed`.
- Separate facts, hypotheses, and recommendations. Preserve useful exact requirements, APIs, errors, versions, constraints, decisions, and observed verification; paraphrase sources except for short exact technical wording.
- Use `[[wikilinks]]` only for known internal notes and Markdown links for external sources. Keep tags and `source_refs` minimal and concrete.
- Remove generic introductions, process narration, repeated conclusions, empty headings, secrets, personal data, and unsupported completion claims.

A standalone note task permits read-only inspection of in-scope code, tests, specifications, reports, logs, and already-observed results. It does not authorize project tests, builds, linters, generators, dependency installation, `adb`, emulators, or simulators. A test file proves intended coverage, not that it passed. Use `待验证` when execution evidence is absent; never upgrade status to obtain a higher quality score.

For project-scoped architecture or simple-change notes, include a compact requirement → design → implementation → verification table only when concrete relationships exist. Use exact IDs, headings, files, symbols, tests, or observed reports; `未实现` and `待验证` are valid honest gaps.

## Quality gate

- Use the lightweight gate for a `captured` learning note or contained simple change with no material risk, project traceability, source conflict, substantial restructure, or diagram trigger.
- Use the full note scorecard for architecture, Bug, learning beyond `captured`, material traceability/risk, source conflicts, substantial restructuring, or a required diagram.
- Evaluate existing evidence only. At most two revisions may follow a non-pass; after a third failure, do not write.

## Safe updates

- Prefer a targeted patch; preserve `created`, update `updated`, and avoid duplicate headings, links, tags, or competing current solutions.
- Copy exact heading paths or block IDs from the document map before patching. Treat any MCP `isError` result as failure.
- Delete, move, rename, or execute Obsidian commands only when explicitly requested. Require exact targets for destructive duplicate cleanup; never use broad cleanup or search-derived wildcards.

Report the note type, action, path, short summary, and read-back result. If Obsidian is unavailable, explain the connection problem and keep the draft local; do not guess the vault path.
