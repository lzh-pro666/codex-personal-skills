# Artifact Quality Gate

Evaluate the delivered artifact and observed evidence, not effort or process narration. This gate never expands authorization to run commands or mutate external systems.

## Routing

Use the **lightweight gate** for a contained, low-risk code change or note. Use the **full scorecard** when an evaluation requests it or the artifact has material architecture, migration, public-contract, data-integrity, security, concurrency, cross-system, or production risk. A truthful verification gap may pass only when the artifact's status and claims remain non-terminal and accurate.

### Lightweight gate

Pass only when all applicable checks have evidence:

- The requested behavior and boundaries are satisfied without unrelated scope.
- Relevant verification passed, or the exact unverified boundary is stated.
- Facts, status, compatibility, and completion claims match the evidence.
- No credible correctness, data-loss, race, privacy, security, credential, or destructive-operation blocker remains.
- The result is concise, maintainable, and free of speculative guards, empty sections, fabricated references, or duplicate canonical knowledge.

Any failed check means `revise`. After two artifact revisions, a third non-pass is `fail`.

## Full scorecard contract

An artifact passes at 85/100 with every dimension minimum met and no blocker. A formal suite also requires an average of 90/100 and every latest artifact to pass. Keep the original `run_id` and `case_id` across revisions; attempts 1–2 may be `revise`, while attempt 3 must be `pass` or `fail`. Do not re-score an unchanged artifact as a new attempt.

Use this JSON shape only for machine-readable requests and evaluation runs:

```json
{
  "run_id": "evaluation-run-identifier",
  "case_id": "identifier",
  "attempt": 1,
  "artifact_type": "code | note | workflow",
  "dimensions": [
    {
      "name": "stable_dimension_id",
      "score": 0,
      "max_score": 0,
      "evidence": ["observed command, file:line, heading, or diagram"],
      "gaps": ["specific missing or weak behavior"]
    }
  ],
  "blockers": [],
  "total": 0,
  "decision": "pass | revise | fail"
}
```

Never award points for intentions. A `pass` requires all thresholds and no blockers.

## Code — 100 points

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `functional_correctness` | Acceptance coverage and observable behavior | 30 | 24 |
| `architecture_maintainability` | Boundaries, cohesion, compatibility, changeability, and justified abstractions | 20 | 0 |
| `tests_verification` | Regression proof, test quality, authorized checks, and honest gaps | 20 | 16 |
| `robustness_security` | Errors, trust boundaries, cancellation, concurrency, privacy, and security | 15 | 0 |
| `readability_naming` | Intent-revealing structure, naming, and useful comments | 10 | 0 |
| `scope_control` | Smallest coherent change that fully satisfies the accepted behavior without unrelated churn | 5 | 0 |

Code blockers include a missing core acceptance criterion; a credible crash, data-loss, race, privacy, or security risk; an incompatible API; fabricated verification; an unsupported bug root cause; testable changed behavior without regression coverage or justification; or confidential material.

Judge scope by necessity and coherence, not changed-line count. Do not penalize required contract, model, migration, compatibility, error-handling, or test work. Reward real boundary validation and useful abstractions; deduct speculative guards, invariant-hiding fallbacks, duplicated checks, and pass-through wrappers.

## Developer note — 100 points

Use the full note scorecard for architecture or Bug notes, learning notes beyond `captured`, material project traceability or risk, authoritative-source conflicts, substantial canonical-note restructuring, or a required diagram.

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `understandability` | A future reader can understand context, mechanism, and conclusion | 25 | 20 |
| `completeness` | Required evidence for the selected note type is present | 25 | 20 |
| `correctness_evidence` | Facts, hypotheses, sources, status, verification, and gaps are accurate | 20 | 16 |
| `searchability_traceability` | Specific title, stable tags, links, sources, and project traceability where relevant | 10 | 0 |
| `structure_concision` | Scannable organization without repetition or empty sections | 10 | 0 |
| `diagrams_examples` | Appropriate examples or diagrams add information | 10 | 0 |

Required content by note type:

- **Architecture**: context, goals/non-goals, constraints, alternatives/trade-offs, decision, components/data flow, failure paths, applicable migration, risks, status, sources, and verification/traceability.
- **Bug**: symptom/impact, reproduction, expected/actual behavior, evidence-backed root cause, fix, regression coverage, residual risk, status, and sources.
- **Learning**: learning question, source boundary or synthesis, mechanism, applicability/version boundary, facts versus inference, useful example or practice evidence, verification status, and sources.
- **Simple change**: goal, scope, change, verification, material risk, status, sources, and project traceability when concrete references exist.

Note blockers include a duplicate canonical note, secret or unsupported conclusion, evidence-contradicted status, unresolved authoritative-source conflict, missing required traceability, or a missing required diagram/equivalent explanation. Test source proves intended coverage, not a passing run; `待验证` cannot support `implemented`, `fixed`, `completed`, or `verified`.

## Diagram and example trigger

Use a diagram or equivalent compact representation only when it materially clarifies three or more components, async/lifecycle timing, three or more state transitions, material decision branches, or three or more alternatives/mappings. It must agree with the text, include relevant failure branches, and add information rather than duplicate prose. Otherwise a relevant example or justified omission may earn the dimension.

## Workflow — 100 points

Use workflow scoring only in formal workflow evaluations, not as an extra deliverable for ordinary tasks.

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `classification_routing` | Correct task class and specialist skill routing | 15 | 12 |
| `requirements_alignment` | Goals, boundaries, constraints, and acceptance | 15 | 12 |
| `implementation_scope` | Safe, minimal, specification-aligned execution | 15 | 0 |
| `verification_strategy` | Proportionate test, static, and manual verification | 20 | 16 |
| `evidence_integrity` | Facts and claims are traceable and honest | 15 | 12 |
| `context_efficiency` | Complete relevant context with bounded loading and low noise | 10 | 8 |
| `handoff_capture` | Clear outcome, evidence, risks, and optional knowledge handoff | 10 | 0 |

Workflow blockers include mutation outside the requested outcome, ignored repository instructions, destructive or external writes outside authority, fabricated evidence, validation commands launched only to embellish documentation, overwritten user changes, broad test cleanup, credential exposure, or production writes during an evaluation.

For context efficiency, reward targeted searches, the complete affected call chain, progressive reference loading, bounded outputs, retained constraints, and source pointers. Do not reward a short but incomplete investigation.
