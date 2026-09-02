# Atomic Patterns

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Atomic

**Module:** `Synchronization` · **Availability:** iOS 18.0+

`Atomic<Value>` provides lock-free atomic operations on values conforming to
`AtomicRepresentable`. Use atomics for simple counters, flags, and
compare-and-swap patterns where a full lock would be overkill. `Atomic`
conforms to `Sendable`, so it can be stored in `Sendable` holder types.

**Documentation:**
[Apple `Atomic`](https://developer.apple.com/documentation/synchronization/atomic)

### Counter Example

```swift
import Synchronization

final class RequestTracker: Sendable {
    let activeRequests = Atomic<Int>(0)

    func beginRequest() {
        activeRequests.wrappingAdd(1, ordering: .relaxed)
    }

    func endRequest() {
        activeRequests.wrappingSubtract(1, ordering: .relaxed)
    }

    var count: Int {
        activeRequests.load(ordering: .relaxed)
    }
}
```

For an independent scalar counter called from C callbacks, `Atomic<Int>` is the
best iOS 18+ standard-library fit because the callback remains synchronous and
does not need an actor hop:

```swift
import Synchronization

@available(iOS 18.0, *)
final class CallbackCounter: Sendable {
    private let value = Atomic<Int>(0)

    func incrementFromCallback() {
        value.wrappingAdd(1, ordering: .relaxed)
    }

    var snapshot: Int {
        value.load(ordering: .relaxed)
    }
}
```

Use `.relaxed` only when the counter is independent and does not publish or
order access to other state. If a flag or counter coordinates access to other
data, use acquire/release ordering or a lock that protects the compound state.

### Boolean Flag

```swift
let isShutdown = Atomic<Bool>(false)

func shutdown() {
    let (exchanged, _) = isShutdown.compareExchange(
        expected: false,
        desired: true,
        ordering: .acquiringAndReleasing
    )
    guard exchanged else { return } // Already shut down
    performCleanup()
}
```

### Memory Ordering

Atomic operations require an explicit memory ordering:

| Ordering | Use case |
|---|---|
| `.relaxed` | Counters, statistics — no ordering guarantees needed |
| `.acquiring` | Read that must see all writes before a corresponding release |
| `.releasing` | Write that must be visible to a corresponding acquire |
| `.acquiringAndReleasing` | Compare-and-swap, read-modify-write |
| `.sequentiallyConsistent` | Strongest guarantee — rarely needed |

**Guideline:** Use `.relaxed` for simple counters. Use
`.acquiringAndReleasing` for compare-and-swap patterns. Avoid
`.sequentiallyConsistent` unless you have a proven need — it is the most
expensive ordering.

### When to Use Atomics vs Mutex

- **Atomics:** Simple independent scalar values (Int, Bool, UInt64), single-field
  counters, flags. Lock-free and very fast. For C callback counters, prefer
  `Atomic` when the app can use iOS 18+ APIs or an accepted package dependency;
  otherwise use `OSAllocatedUnfairLock`.
- **Mutex:** Compound state (dictionaries, structs with multiple fields),
  multi-step operations that must be atomic as a group.
