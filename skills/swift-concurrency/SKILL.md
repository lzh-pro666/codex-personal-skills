---
name: swift-concurrency
description: Diagnose or implement Swift concurrency code involving actor isolation, Sendable, tasks, cancellation, AsyncSequence, continuations, locks, or strict-concurrency migration. Use for concurrency compiler diagnostics and data-race or async-lifecycle problems; do not trigger for ordinary synchronous Swift changes.
---

# Swift Concurrency

Resolve the concrete concurrency problem with the smallest behavior-preserving change. Do not assume a Swift language mode, default actor isolation, deployment target, or toolchain version.

## Workflow

1. Capture the exact diagnostic or runtime failure and identify the affected target.
2. Inspect `SWIFT_VERSION`, strict-concurrency/default-isolation settings, deployment target, and nearby conventions. In siuper-ios, preserve iOS 17 compatibility and mixed Swift 5/6 targets unless the target proves otherwise.
3. Trace the state and isolation boundary before editing: owner, readers, writers, suspension points, task lifetime, and cancellation path.
4. Prefer static isolation and structured concurrency over suppression annotations or detached work.
5. Build or test the smallest affected target and verify cancellation/error behavior when relevant.

## Decision Rules

- Put UI state and UI mutations on `@MainActor`; do not move unrelated networking or CPU work there.
- Prefer immutable `Sendable` values or actor-owned mutable state. Treat `@unchecked Sendable`, `nonisolated(unsafe)`, and `@preconcurrency` as audited escape hatches, not default fixes.
- Do not recommend `@concurrent`, default MainActor isolation, `Task.immediate`, typed throws, or other versioned APIs until the target toolchain and language mode support them.
- Preserve existing GCD/Combine interoperability when a narrow fix is sufficient; migrate it only when requested or required for correctness.
- Prefer `Task`, `async let`, or task groups according to lifetime and fan-out. Use `Task.detached` only when breaking inherited actor, priority, task-local, and cancellation context is intentional.
- Never hold a lock across `await`. Do not add a lock inside an actor.
- Treat actor state as mutable across every suspension point and make cancellation cooperative.

## Load References Only When Needed

- Compiler diagnostics or migration settings: `references/diagnostics.md`
- Approachable concurrency and versioned language features: `references/approachable-concurrency.md`
- Swift 6.2+ language behavior, advanced actor patterns, or migration design: `references/concurrency-patterns.md`
- SwiftUI task and observation behavior: `references/swiftui-concurrency.md`
- Continuations, delegates, Objective-C, or GCD bridging: `references/bridging-interop.md`
- Mutex, atomics, or synchronous callback protection: `references/synchronization-primitives.md`
- Debounce, throttle, merge, or other AsyncAlgorithms use: `references/async-algorithms.md`

The core rules above are sufficient for ordinary actor isolation, task ownership, cancellation, and Sendable fixes. Read a reference only when the task needs its specialized API or migration detail, and verify version-sensitive claims against the installed SDK/toolchain.

## Completion Check

- The original diagnostic or race has a concrete explanation.
- The fix does not widen isolation or availability requirements unnecessarily.
- Task ownership, cancellation, errors, and suspension-point invariants remain correct.
- Targeted build/tests pass, or the exact verification gap is reported.
