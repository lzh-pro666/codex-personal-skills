---
name: developer-notes
description: Create, search, deduplicate, organize, and safely update developer notes in Obsidian through the obsidian MCP. Use when the user asks to 整理、沉淀、记录、保存、查找或更新 development work, especially 需求架构设计, Bug 修复, or 简单需求处理 for iOS and software-engineering tasks. Classify the work into exactly one of these three note types, load only its matching template, search before writing, update or create without duplication, and verify every write.
---

# 开发笔记

Turn completed or planned development work into concise, reusable Obsidian notes. Use the configured `obsidian` MCP for all vault operations.

## Fast path

1. Classify the request as search-only or write.
2. For a write, choose exactly one note type using the rules below.
3. Extract 3–6 high-signal terms and search before writing.
4. Read only the 3–5 best candidates.
5. Update the canonical note when the same work already exists; otherwise create one note.
6. Read exactly one matching template before writing.
7. State the target path and create/update action, make the smallest safe change, then read back and verify.

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

- Search titles, paths, tags, properties, and content using exact APIs, errors, feature names, project names, symptoms, and solution terms.
- Try Chinese and English variants only when useful.
- Rank by same note type, topic, context, solution, then recency.
- Return at most five results by default: path, match reason, and one-line summary.
- Do not list or scan the whole vault when targeted search is available.
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
- Omit unknown optional properties such as `aliases`, `project`, and `severity`; never write placeholder values such as `<可选>`.
- Preserve exact requirements, APIs, errors, code, logs, versions, constraints, decisions, and verification evidence when useful.
- Separate confirmed facts from hypotheses.
- Add `[[wikilinks]]` only for known or deliberately created internal notes; use Markdown links for external sources.
- Keep tags stable and minimal.
- Never write secrets, credentials, personal data, or unrelated confidential content.
- Remove generic introductions, process narration, repeated conclusions, and empty headings.

## Update safely

- Prefer a targeted patch over rewriting the full note.
- Preserve `created`; update `updated`; merge tags and links without duplicates.
- Avoid duplicate headings, repeated code, and conflicting current solutions.
- Use version or match controls when available.
- Do not delete, move, rename, or execute Obsidian commands unless explicitly requested.

## Report briefly

Report the selected note type, action, path, one-line change summary, and verification result. Do not reproduce the full note unless asked.

## If Obsidian is unavailable

Explain that the `obsidian` MCP could not be reached. Ask the user to keep Obsidian and Local REST API with MCP running, then reconnect Codex. Do not guess a vault path.
