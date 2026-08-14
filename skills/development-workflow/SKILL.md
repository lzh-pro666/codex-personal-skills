---
name: development-workflow
description: Use when a software request involves requirements or architecture design, diagnosis without a fix, code review, implementation, bug fixing, refactoring, or tests, especially for iOS work that may involve OpenSpec, Swift concurrency, testing, interoperability, accessibility, or knowledge capture.
---

# Development Workflow

Deliver verified outcomes with the smallest justified process. This is a Codex policy overlay and specialist router, not a copy of Superpowers: load another workflow only when its own trigger matches. Repository code, tests, accepted specifications, and observed verification are facts; notes are a reusable knowledge layer.

## Route and authority

Choose the requested outcome before mutation:

- **Design-only**: deliver requirements, alternatives, trade-offs, and acceptance; write only a requested design artifact.
- **Diagnose-only**: reproduce or inspect, confirm or bound the cause, and report without fixing.
- **Review-only**: report actionable findings without editing, posting comments, or changing external state.
- **Code change**: implementation is explicitly requested. Classify it as **complex/architecture**, **bug fix**, or **simple change**.

Read-only wording such as “inspect,” “explain,” “diagnose,” “review,” or “do not modify” is a hard mutation boundary. Do not edit tracked/configuration files, create branches, stage, commit, push, publish notes, or implement a fix. If proof requires mutation, report the limitation and request authority.

Independently mark work **high-risk** when it is security-sensitive, destructive, production-data or migration work, a public-contract change, cross-system coordination, or consequential external state.

## Align only what matters

- For an ambiguous complex requirement, use `$brainstorming` only when its trigger independently matches and it is already available. Skip precise tasks and accepted specifications. Never interrupt work or restart Codex to load a Skill; otherwise ask only questions whose answers change scope or architecture.
- Record relevant goals, non-goals, constraints, trade-offs, failure behavior, migration, and observable acceptance. When required, accepted OpenSpec is authoritative; link its `change-id` and stop on a conflict before implementation.
- For a bug, capture the shortest reproduction, expected/actual behavior, evidence, and a falsifiable root-cause hypothesis. Use `$systematic-debugging` only when the cause is unclear, intermittent, disputed, or previously misdiagnosed.
- For a simple change, state intended behavior, affected surface, non-goals, and minimum verification. Do not create ceremony without decision value.

## Implement scoped changes

Enter this section only for **Code change** mode.

1. Read repository instructions, inspect the affected path, and check worktree status. Never store credentials. Treat existing modifications as user-owned; use an isolated worktree when requested or when overlap, duration, concurrency, or risk materially warrants it. Never reset or overwrite user work.
2. Load only matching specialist Skills:
   - actor isolation, tasks, cancellation, races: `$swift-concurrency`
   - Swift tests or framework migration: `$swift-testing`
   - SwiftUI/UIKit boundaries: `$swiftui-uikit-interop`
   - assistive technologies and accessible UI: `$ios-accessibility`
3. Search narrowly, inspect the affected call chain, bound logs and diffs, and load only references needed for the current decision. Preserve accepted constraints and evidence across compaction; re-read the authoritative source when exact wording matters.
4. State a brief outcome-oriented plan and acceptance for non-mechanical work. Use `$writing-plans` only when requested, required by high risk, or needed for resumable dependency coordination. A plan never grants implementation authority.
5. Keep the patch minimal and compatible. Defend untrusted boundaries and observed failures, but do not add speculative guards for impossible states or hide programmer errors behind silent fallbacks. Extract helpers only for meaningful reuse, non-obvious rules, side effects, real branching, or test seams; avoid pass-through wrappers and needless single-use helpers.
6. Use `$test-driven-development` when requested or required, or when a cheap focused red test disambiguates implementation or captures a confirmed regression. An accurate existing failure may be red. Do not force it for behavior-preserving refactors, documentation, configuration-only work, generated code, prototypes, pure layout, or impractical unit-test boundaries; use targeted builds and concrete manual acceptance instead.

## Verify, evaluate, and finish

- Run the narrowest relevant checks before repository-required checks. Reuse fresh evidence while inputs are unchanged; later mutation invalidates only affected evidence. Never claim an unobserved pass.
- Use `$verification-before-completion` for high-risk, disputed, or multiple independent material claims; routine command count alone does not trigger it.
- After a code change, read `references/artifact-quality.md` and produce its evidence-backed scorecard. Include context-control evidence: relevant sources loaded, bounded searches, retained constraints, and excluded irrelevant output. Do not score nonexistent generated code for design-, diagnose-, or review-only work.
- On `revise`, address material gaps and re-evaluate, with at most two revisions. After a third non-pass, report blockers and preserve the last safe state; do not claim completion.
- Report outcome, verification, quality decision, risks, and unverified boundaries. After a passing implementation, ask whether to create an Obsidian development note; never write one automatically. When requested, use `$developer-notes` with verified facts. Use `$pr-review-to-notion` for a single-PR retrospective rather than duplicating it in Obsidian.
