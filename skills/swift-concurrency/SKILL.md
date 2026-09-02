---
name: swift-concurrency
description: Diagnose or implement Swift concurrency involving actor isolation, Sendable, tasks, cancellation, AsyncSequence, continuations, locks, or strict-concurrency migration. Use for compiler diagnostics, races, and async-lifecycle problems, not ordinary synchronous Swift changes.
---

# Swift Concurrency

Resolve the concrete concurrency problem with the smallest behavior-preserving change. Confirm the target's Swift mode, isolation settings, deployment target, and toolchain before using versioned behavior.

## Decisions

- Trace the state owner, readers/writers, isolation boundary, suspension points, task lifetime, cancellation, and error path.
- Keep UI state and mutations on `@MainActor` without moving unrelated network or CPU work there. Prefer immutable `Sendable` values or actor-owned mutable state.
- Treat `@unchecked Sendable`, `nonisolated(unsafe)`, `@preconcurrency`, and detached tasks as audited escape hatches.
- Choose `Task`, `async let`, or task groups by lifetime and fan-out. Preserve existing GCD/Combine interop when a narrow fix is sufficient.
- Never hold a lock across `await` or add a lock inside an actor. Revalidate actor state after suspension and keep cancellation cooperative.

## References

- Diagnostics and migration settings: `references/diagnostics.md`
- Approachable-concurrency settings: `references/approachable-concurrency.md`
- Complete approachable-concurrency examples: `references/concurrency-approachable-examples.md`
- Task startup, cleanup, isolated conformances, weak capture, or transactional observation: `references/concurrency-versioned-features.md`
- Global/static state or target-wide migration: `references/concurrency-migration-state.md`
- SwiftUI tasks and observation: `references/swiftui-concurrency.md`
- Continuations, delegates, Objective-C, or GCD: `references/bridging-interop.md`
- Mutex or OSAllocatedUnfairLock: `references/mutex-locks.md`
- Atomics and memory ordering: `references/atomics.md`
- Actor-versus-lock selection: `references/synchronization-selection.md`
- AsyncAlgorithms operators: `references/async-algorithms.md`

Use `references/concurrency-patterns.md` or `references/synchronization-primitives.md` only as routers for mixed requests. Read only the specialized reference needed by the problem and verify version-sensitive claims against the installed SDK/toolchain.

Finish with a concrete explanation of the original diagnostic/race, narrow authorized verification, and explicit cancellation/error/availability gaps.
