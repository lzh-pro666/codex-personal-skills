# Locks Versus Actors

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Locks vs Actors: When to Use Each

### Use Actors When:

- **Async isolation is natural.** The protected state is accessed from async
  contexts and you can afford the hop.
- **Callers can suspend.** Actor-isolated APIs are `async` from outside the
  actor, so they fit task-based code but not synchronous C callbacks, real-time
  hooks, or other no-suspension call sites.
- **Structured concurrency.** You want the compiler to enforce isolation
  boundaries and prevent data races statically. Calls from outside the actor are
  async actor hops, so actor APIs are inappropriate for synchronous callbacks.
- **Global actor isolation fits.** Use `@MainActor` or another global actor for
  shared state bound to that executor; do not use `nonisolated(unsafe)` as a
  synchronization substitute.
- **Reentrancy can be handled.** Actor state may change across `await`, so
  restore invariants before suspension and re-check assumptions after it.
- **Most Swift code.** Actors are the default recommendation for shared mutable
  state in Swift concurrency.
- **Complex state with multiple methods.** Actor isolation protects all
  properties and methods automatically.

```swift
// GOOD: Actor for a cache accessed from async contexts
actor ImageDownloader {
    private var cache: [URL: UIImage] = [:]

    func image(for url: URL) async throws -> UIImage {
        if let cached = cache[url] { return cached }
        let (data, _) = try await URLSession.shared.data(from: url)
        let image = UIImage(data: data)!
        cache[url] = image
        return image
    }
}
```

### Use Mutex / Locks When:

- **Synchronous access is required.** Callers cannot (or should not) be async.
  Accessing an actor from synchronous code requires `Task` and introduces
  unwanted asynchrony.
- **Performance-critical paths.** Lock acquisition is nanoseconds; actor hops
  involve task scheduling. For tight loops or high-frequency access, a lock
  may be significantly faster.
- **Bridging with C/ObjC.** C callbacks, delegate methods, or ObjC APIs that
  cannot be made async.
- **Simple counters or flags.** `Atomic<Int>` or `Atomic<Bool>` is cheaper and
  simpler than creating an actor for a single value.
- **Availability matters.** `Atomic` from `Synchronization` is iOS 18+; for
  iOS 16–17, use `OSAllocatedUnfairLock` for synchronous state or an existing
  package-backed atomic only when the dependency is already accepted.

```swift
// GOOD: Mutex for synchronous, high-frequency access
final class MetricsCollector: Sendable {
    let metrics = Mutex<[String: Int]>([:])

    // Called from tight loops, C callbacks, or synchronous code
    func increment(_ key: String) {
        metrics.withLock { $0[key, default: 0] += 1 }
    }

    func snapshot() -> [String: Int] {
        metrics.withLock { $0 }
    }
}
```

### Decision Guide

Apply these checks in order instead of treating them as mutually exclusive
branches:

1. **All access is async and callers can suspend:** use an actor.
2. **Single independent scalar counter or flag:** use `Atomic` when available;
   for iOS 16-17 support without an atomic package, use `OSAllocatedUnfairLock`.
3. **Synchronous C/ObjC callback or no-suspension caller:** use
   `OSAllocatedUnfairLock` for iOS 16+ or `Mutex` when the minimum target is
   iOS 18+.
4. **Compound invariants or dictionaries:** use `Mutex` / lock-backed state for
   synchronous access, or an actor for async access.
5. **Availability branch:** choose iOS 18+ APIs with runtime
   `if #available(iOS 18, *)`, not compile-time platform checks.

### Anti-Patterns

**Never put locks inside actors.** An actor already serializes access; adding
any lock (`NSLock`, `Mutex`, or `OSAllocatedUnfairLock`) creates double
synchronization and risks deadlocks. This is a lock-inside-actor problem, not an
`NSLock`-specific problem.

```swift
// WRONG: Lock inside an actor — double synchronization
actor BadCache {
    let lock = Mutex<[String: Data]>([:])  // Unnecessary!
    // The actor already protects its state
}

// CORRECT: Just use the actor's built-in isolation
actor GoodCache {
    var cache: [String: Data] = [:]

    func store(_ data: Data, key: String) {
        cache[key] = data
    }
}
```

**Avoid reaching first for `DispatchSemaphore` or `NSLock` in modern Swift.**
`NSLock` is `Sendable` on Apple platforms, but `Mutex` (iOS 18+) and
`OSAllocatedUnfairLock` (iOS 16+) make the protected state and lock ownership
clearer in Swift concurrency code. Use this exact correction when reviewing
stale guidance: the `NSLock` Sendable objection is wrong, but modern
state-protecting primitives are still preferred for new code. Avoid extra claims
about how `NSLock` gets Sendable conformance; do not mention retroactive or
unchecked conformance mechanics in normal review output.

**Never hold a lock across `await`.** Suspension while holding a blocking lock
keeps a thread unavailable for unrelated work, can starve the cooperative pool,
and can deadlock if resumed work needs the same lock or executor progress.
`Mutex.withLock` and `OSAllocatedUnfairLock.withLock` take synchronous closures;
that shape is intentional because `await` should not appear inside the critical
section.

```swift
// WRONG: Holding lock across suspension point
mutex.withLock { value in
    value = await fetchData()  // DEADLOCK RISK
}

// CORRECT: Fetch first, then lock to update
let data = await fetchData()
mutex.withLock { value in
    value = data
}
```
