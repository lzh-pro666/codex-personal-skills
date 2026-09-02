# Siuper Project Locations and Cross-Project Isolation

Use these local roots only as location hints:

- Android: `/Users/admin/project/siuper-sdk-android`
- iOS: `/Users/admin/Desktop/project/siuper-ios`

The repository containing the current task is the primary workspace. The counterpart repository is a read-only evidence source unless the user explicitly authorizes a separately scoped change there. If a configured path is missing, report that fact; do not search the home directory or other broad locations for a replacement.

## When Counterpart Access Is Justified

Do not open the counterpart repository merely because it is available or because the current task targets Android or iOS. Access it only when either condition holds:

1. The user explicitly asks for cross-platform comparison, parity, migration, or reuse.
2. A concrete shared API, protocol, data-model, or product-behavior ambiguity cannot be resolved from the current repository, and counterpart code is likely to provide the cheapest relevant evidence.

Before using the second condition, state the unresolved question, why the current repository is insufficient, and which symbol, feature, or narrow path will be inspected. A general desire to learn the other platform's implementation is not sufficient.

## Bounded Read Protocol

1. Inspect the current repository and identify the exact evidence gap first.
2. Confirm the configured counterpart root exists without enumerating unrelated parent directories.
3. Search for an exact symbol, protocol name, endpoint, model, or feature term. Constrain searches by likely module and file type, and keep returned matches bounded.
4. Open only the minimum definition, caller, test, or configuration files needed to answer the question. Expand one dependency hop at a time only when the prior evidence leaves a named gap.
5. Stop as soon as the cross-project question is answered, and retain concise source paths rather than large file dumps.

Do not run builds, tests, dependency resolution, generators, indexers, or broad Git-history searches in the counterpart repository unless the user explicitly requests that operation for that repository. Do not change its branch, create a worktree, stage files, or edit files as a side effect of a lookup.

Counterpart behavior is comparative evidence, not authority for the current project. Preserve the current repository's accepted requirements, public contracts, dependency versions, architecture, and instructions; call out meaningful differences instead of copying the other implementation mechanically.
