# Notion Contract

## Target

Resolve the target at runtime from `skills/pr-review-to-notion/config/notion.local.json`, which is ignored by Git. Copy `notion.local.example.json` to that filename and set `data_source_name` and `data_source_url`. Never commit the real URL when it identifies a private workspace.

If the local file is absent or incomplete, stop before writing and return the validated draft. Do not guess a database from prior conversations or other projects.

## Required Properties

| Property | Type | Value |
| --- | --- | --- |
| `标题` | Title | Chinese result-oriented summary; do not copy the raw PR title |
| `PR 链接` | URL | Canonical GitHub PR URL |
| `原PR标题` | Rich text | Exact GitHub PR title |
| `总结` | Rich text | Behavior change plus core improvement |
| `学习` | Rich text | Reusable practice plus prevention lesson |
| `优化` | Rich text | One to three evidence-based risks/alternatives, or `未发现明确优化项` |

Keep each rich-text value below 1,800 characters. Put detailed evidence in the page body.

## Write Preflight

1. Run `validate_draft.py` after the final body and properties are assembled. It scans both `retrospective.md` and `notion-properties.json`.
2. Treat known credential formats, private-key headers, Authorization values, credential-labelled values, email addresses, international phone numbers, and Chinese mobile numbers as blocking findings. Replace only the sensitive value with `[REDACTED_SECRET]`, `[REDACTED_EMAIL]`, or `[REDACTED_PHONE]`, then rerun validation. Never echo a match while reporting the failure.
3. Keep canonical PR URLs, GitHub logins, review IDs, paths, and ordinary unlabeled 40/64-character Git or content hashes. A hash without credential context is not a secret.
4. Read the live data source schema and verify all six names and types.
5. Search the target data source for the exact `PR 链接`.
6. If a matching page exists, do not create or update automatically; ask the user which action to take.

## Write and Verify

- Create one page with all six properties and the complete Markdown body when the connector supports an atomic create.
- Otherwise create the page with properties, append the body, and report the page URL if appending fails. Never create a second page as an automatic retry.
- Read the created page back. Confirm `标题`, `PR 链接`, and the first required body heading.
- Report success only after read-back verification.
