---
name: development-workflow
description: Use when a software request involves requirements or architecture design, diagnosis without a fix, code review, implementation, bug fixing, refactoring, or tests, especially for iOS work that may involve OpenSpec, Swift concurrency, testing, interoperability, accessibility, or knowledge capture.
---

# Development Workflow

Deliver verified code with the smallest justified process. Treat repository code, tests, accepted specifications, and executed verification as facts; treat notes as a reusable knowledge layer, not as implementation authority.

## Route the work

Choose the execution mode from the user's requested outcome before editing:

1. **Design-only**: Analyze requirements, constraints, alternatives, trade-offs, and acceptance criteria; deliver a design without implementing it. If the user explicitly asks to save a design artifact, write only that artifact.
2. **Diagnose-only**: Reproduce or inspect the symptom, determine the root cause and evidence, and report findings without applying a fix.
3. **Review-only**: Inspect the requested diff or artifact and report actionable findings without editing files, posting comments, or changing repository/external state.
4. **Code change**: The user explicitly asks to implement, fix, refactor, or otherwise modify code or configuration. Classify this mode into exactly one change type:
   - **Complex requirement or architecture change**: Cross-module behavior, new API/data model, migration, compatibility strategy, material trade-offs, or unclear acceptance criteria.
   - **Bug fix**: Incorrect behavior, crash, regression, failed test, performance defect, race, incident, or compatibility failure.
   - **Simple change**: Contained and low-risk work with clear acceptance criteria and no architectural decision.

Read-only wording such as “inspect,” “explain,” “diagnose,” “review,” or “do not modify” is a hard mutation boundary. For these requests, use read-only inspection and non-mutating diagnostics; do not implement, edit tracked/configuration files, create branches, stage, commit, push, post comments, or publish notes. If proof requires mutation, report that limitation and request authorization. Permission to save a design artifact does not authorize code changes.

A requested code change remains one of the three change types: a bug remains a bug even when its fix affects architecture, and a simple change escalates only when investigation reveals a material design decision.

## Align requirements

- For a complex requirement, explicitly use Superpowers `$brainstorming` when it is available in the current task. Never interrupt an active task or require a Codex restart merely to load it. If unavailable, perform the same focused requirements-alignment questions in this workflow; do not create a second alignment Skill.
- Record goal, non-goals, users, constraints, alternatives, trade-offs, failure behavior, migration, and observable acceptance criteria.
- When the repository contains `openspec/` or its instructions require OpenSpec, treat the accepted OpenSpec change as authoritative. Link any Superpowers artifact to the OpenSpec `change-id`. If they conflict, stop and correct OpenSpec before implementation.
- For a bug, capture the shortest reproduction, expected/actual behavior, affected versions, evidence, and a root-cause hypothesis before editing.
- For a simple change, state the intended behavior, affected surface, explicit non-goals, and minimum verification. Do not create design ceremony with no decision value.

## Inspect and implement

Enter this section only for **Code change** mode. Design-only, diagnose-only, and review-only stop after delivering the requested analysis, evidence, design, or findings.

1. Read repository instructions, inspect the complete affected path, and run a read-only worktree status check before changing code.
   - Never write, stage, or commit a credential. Replace it with an ignored local configuration, environment variable, or approved credential store before any implementation step.
   - Treat every pre-existing modification as user-owned. If the worktree is dirty, use a separate worktree for broad integration or any change that could overlap; for a small non-overlapping edit, preserve the existing changes and explicitly verify no overlap. Never reset or overwrite them.
2. Load only relevant specialist Skills:
   - Swift actor isolation, tasks, cancellation, or races: `$swift-concurrency`
   - Unit tests or framework migration: `$swift-testing`
   - SwiftUI/UIKit boundaries: `$swiftui-uikit-interop`
   - Assistive technologies or accessible UI: `$ios-accessibility`
   - Use targeted search before broad listing, read the affected call chain rather than unrelated directories, and load only the reference files needed for the current decision. Bound logs, diffs, search results, and external evidence; keep a source pointer when summarizing material that may be needed later.
   - Preserve accepted goals, non-goals, constraints, unresolved questions, and verification evidence across long tasks or context compaction. Re-check the authoritative source instead of relying on a lossy summary when a decision depends on exact wording.
3. Keep the patch scoped to the accepted behavior. Preserve compatibility and local conventions unless the specification explicitly changes them.
   - Defend untrusted boundaries and observed failure paths: user/network input, decoding, persistence, concurrency, permissions, and security-sensitive operations.
   - Do not add speculative guards for states already made impossible by types or established invariants. Never hide a programmer error behind an empty result, silent return, or broad fallback; enforce or document the invariant instead.
   - Extract a helper only when it provides meaningful reuse, names a non-obvious rule, isolates a side effect, reduces real branching, or creates a useful test seam. Avoid one-line pass-through helpers, single-use wrappers, and layers that merely rename an existing API.
4. At every testable boundary—models, view models, services, business rules, parsers, state machines, and regressions—first demonstrate a failing test, then make it pass, then run focused regression tests.
5. For pure layout, configuration, generated code, or behavior that cannot reasonably be unit-tested, use targeted builds and concrete manual acceptance steps. Record why an automated test was not suitable.

## Verify and evaluate

- Run the narrowest relevant tests/builds first, then the repository-required checks.
- Do not claim a command passed unless it was executed in the current worktree and its result was observed.
- After verification, read `references/artifact-quality.md` and evaluate the generated code with an evidence-backed scorecard.
- Evaluate context control with observable evidence: relevant files/references loaded, bounded searches or selectors used, critical constraints retained, and irrelevant raw output excluded. Do not reward shallow inspection merely because it used fewer tokens.
- If the decision is `revise`, address every material gap and re-evaluate. Allow at most two revisions (three total evaluations).
- If the third evaluation does not pass, do not claim completion. Report the remaining blockers and preserve the last safe state.

## Finish and capture knowledge

Report outcome, verification evidence, quality decision, risks, and unverified boundaries. After a passing implementation, proactively ask whether the user wants an Obsidian development note. Do not write one automatically.

When requested, invoke `$developer-notes` with the verified facts, source references, quality evidence, and final status. For a PR-focused personal retrospective, use `$pr-review-to-notion`; do not duplicate its full body in Obsidian.
