# Artifact Quality Gate

Use this rule after implementation verification and before delivering generated code or writing a developer note. Evaluate the artifact itself, not the effort or process narration. A score without concrete evidence is invalid.

## Scorecard contract

Produce JSON compatible with this shape when a machine-readable scorecard is requested or an evaluation case is being run:

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
      "evidence": ["test output, file:line, heading, or diagram"],
      "gaps": ["specific missing or weak behavior"]
    }
  ],
  "blockers": [],
  "total": 0,
  "decision": "pass | revise | fail"
}
```

Use `pass` only when every threshold passes and blockers are empty. Use `revise` for remediable gaps during the first three evaluations. Use `fail` after the third unsuccessful evaluation or for an unsafe/unrecoverable result. Cite observed evidence; never award points for intentions.

Keep the same `run_id` and `case_id` across revisions and increment `attempt` from 1 to 3. Attempts 1–2 may be `revise`; attempt 3 must be `pass` or `fail`, never `revise`. Do not evaluate an unchanged artifact as a new attempt.

## Generated code — 100 points

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `functional_correctness` | Acceptance coverage and observable behavior | 30 | 24 |
| `architecture_maintainability` | Boundaries, cohesion, compatibility, changeability, and justified abstractions | 20 | 0 |
| `tests_verification` | Regression proof, test quality, builds, and honest gaps | 20 | 16 |
| `robustness_security` | Errors, boundaries, cancellation, concurrency, privacy, and security | 15 | 0 |
| `readability_naming` | Intent-revealing structure, naming, and useful comments | 10 | 0 |
| `scope_control` | Smallest coherent change without unrelated churn, speculative guards, or trivial wrappers | 5 | 0 |

An individual artifact passes at 85 or above; an evaluation suite passes at an average of 90 or above. Code blockers include:

- Missing a core acceptance criterion.
- A credible crash, data-loss, race, privacy, or security risk.
- Use of nonexistent or incompatible APIs.
- A claimed test/build result without observed execution evidence.
- A bug fix without a root-cause explanation supported by evidence.
- Testable changed behavior without a regression test or a concrete justification.
- A secret, credential, personal datum, or unrelated confidential content.

During maintainability analysis, distinguish necessary boundary protection from defensive ceremony. Reward validation at real trust boundaries and explicit handling of observed failures. Deduct for guards against type-impossible states, silent fallbacks that conceal invariant violations, duplicated checks with no new boundary, and helpers that only forward one call or rename one expression. Do not penalize a short helper when it names a domain rule, centralizes repeated behavior, isolates a side effect, or creates a meaningful test seam.

## Developer note — 100 points

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `understandability` | A future reader can understand context, mechanism, and conclusion | 25 | 20 |
| `completeness` | Required evidence for the selected note type is present | 25 | 20 |
| `correctness_evidence` | Facts, hypotheses, sources, status, and verification are accurate | 20 | 16 |
| `searchability_traceability` | Specific title, stable tags, links, project/source references | 10 | 0 |
| `structure_concision` | Scannable organization without repetition or empty sections | 10 | 0 |
| `diagrams_examples` | Appropriate diagrams/examples add information rather than decoration | 10 | 0 |

A note passes at 85 or above; a note evaluation suite passes at an average of 90 or above. Judge completeness by note type:

- Architecture: context, goal/non-goals, constraints, alternatives/trade-offs, decision, components/data flow, failure paths, migration where applicable, risks, verification, status, and sources.
- Bug: symptom/impact, reproduction, expected/actual result, root cause and evidence, fix, meaningful code/config changes, regression coverage, residual risk, status, and sources.
- Simple change: goal, scope/non-goals where needed, implemented change, verification, material risk, status, and sources.

Do not create empty sections to simulate completeness. Note blockers include secrets, unsupported conclusions, a status contradicted by evidence, a duplicate canonical note, and a required diagram or equivalent explanation being absent.

## Diagram and example analysis

Reward information gain, not diagram count:

- Three or more components or a cross-layer dependency: architecture or data-flow diagram.
- Async calls, event timing, or lifecycle behavior: sequence diagram.
- Three or more states and transitions: state diagram.
- Material decision branches: flowchart.
- Three or more alternatives, mappings, or repeated-field comparisons: table.

A diagram must render, use labels consistent with the code/text, have a short introduction and interpretation, include material dependencies and failure branches, and agree with the written conclusion. Penalize decorative diagrams, duplicated prose, invented edges, and unverifiable detail.

Simple changes and simple bugs do not require a diagram by default. When none of the triggers applies, record a concise omission reason and award the diagram dimension based on suitable examples or the justified omission. When a trigger applies, require the relevant diagram or an equally clear textual representation.

## Workflow — 100 points

| Dimension ID | Criterion | Max | Minimum |
| --- | --- | ---: | ---: |
| `classification_routing` | Correct task class and specialist Skill routing | 15 | 12 |
| `requirements_alignment` | Goals, boundaries, constraints, and acceptance criteria | 15 | 12 |
| `implementation_scope` | Safe, minimal, specification-aligned execution | 15 | 0 |
| `verification_strategy` | Proportionate test/build/manual verification | 20 | 16 |
| `evidence_integrity` | Facts and claims are traceable and honest | 15 | 12 |
| `context_efficiency` | Complete relevant context with bounded loading, durable constraints, and low noise | 10 | 8 |
| `handoff_capture` | Clear delivery, remaining risks, and optional note handoff | 10 | 0 |

Workflow passes at 85 or above and has no blocker. Block on implementation before required alignment/approval, ignored repository instructions, destructive or external writes outside authorization, fabricated verification, or automatic note publication without consent.
Also block on credential material being written or staged, pre-existing user changes being overwritten, broad test cleanup, or a production Notion mutation during an evaluation.

For `context_efficiency`, require evidence rather than token-count claims. Reward targeted searches, complete inspection of the affected call chain, progressive loading of only relevant Skill references, bounded log/diff/review selectors, source pointers for summaries, and retention of accepted constraints across a long task. Deduct for full-repository or full-vault dumps when a targeted query exists, loading unrelated references, repeating large raw outputs, losing a critical constraint during summarization, or producing a verbose handoff that hides the decision. Do not reward an incomplete investigation merely because it is short.
