---
name: development-workflow
description: Use for software requirements or architecture design, diagnosis, code review, implementation, bug fixing, refactoring, or tests. Apply a shared delivery workflow, then load only the relevant platform specialist skill.
---

# Development Workflow

Deliver the requested software outcome with proportionate alignment, implementation, and verification. Repository instructions, accepted specifications, code, tests, and observed results are authoritative; notes are derived knowledge.

## Choose the outcome

- **Design**: define requirements, alternatives, trade-offs, failure behavior, migration, and acceptance without implementing.
- **Diagnose**: establish or bound the cause and report evidence without fixing.
- **Review**: report actionable findings without editing or posting externally.
- **Documentation**: create the requested artifact from existing sources. Do not run project commands merely to make the document look verified.
- **Code change**: implement the requested behavior; classify it as architecture/complex, bug fix, or simple change.

Treat security-sensitive, destructive, migration, public-contract, production-data, and cross-system work as high risk regardless of change size. Read-only wording is a mutation boundary.

## Align before editing

- State the goal, scope, non-goals, observable acceptance, and material assumptions. Ask only when an unresolved answer would change behavior, architecture, compatibility, scope, or authority.
- For a material design choice, recommend an approach and expose its key trade-off before committing to it. Follow accepted OpenSpec or other repository-required specifications.
- For a bug, capture the shortest reproduction, expected/actual behavior, supporting evidence, and a falsifiable root-cause hypothesis.
- For a simple change, keep alignment brief and avoid design ceremony.

## Implement

1. Read repository instructions and inspect the affected call chain and worktree state.
2. Load only the specialist skills needed by the changed surface:
   - Siuper Android architecture, StateFlow/ViewModel, lifecycle, Compose/View, or Gradle tests: `$android-kotlin-mvvm`
   - Android insets/IME, Intent security, or R8: add `$edge-to-edge`, `$android-intent-security`, or `$r8-analyzer` respectively
   - Swift concurrency: `$swift-concurrency`
   - Swift tests: `$swift-testing`
   - SwiftUI/UIKit boundaries: `$swiftui-uikit-interop`
   - iOS accessibility: `$ios-accessibility`
3. Make the smallest coherent change that fully satisfies the accepted behavior. Preserve compatibility unless the requirement changes it; include necessary contract, model, migration, error-handling, and focused-test work. Avoid unrelated refactors, speculative guards, silent fallbacks, and wrappers without a real rule, side effect, branch, reuse, or test seam.
4. Add focused tests for stable, testable behavior or regressions. For configuration, generated output, prototypes, pure layout, or impractical unit boundaries, use targeted static checks and concrete manual acceptance instead.

For configured Siuper project roots and cross-project isolation, read `references/project-locations.md` only when cross-platform evidence is explicitly requested or a named shared-contract ambiguity cannot be resolved locally.

## Verify and evaluate

- Run the narrowest authorized checks that faithfully cover the changed behavior, followed by repository-required checks. Do not run a project build unless the user explicitly requests it or repository instructions require it for the changed surface.
- Map every material completion claim to observed test, static, inspection, or manual evidence; report unverified boundaries precisely.
- Read `references/artifact-quality.md` after a code change. Use its lightweight gate for contained low-risk work and its full 100-point scorecard for formal evaluations, high-risk work, or material architecture, migration, public-contract, data-integrity, security, or concurrency changes. Emit machine-readable JSON only when requested or required by an evaluation.
- A full-gate `revise` result allows at most two artifact revisions. After a third non-pass, report blockers and do not claim completion.
- Report the outcome, verification, risks, and quality decision. Create a development note only when requested; use `$pr-review-to-notion` for a single-PR retrospective.
