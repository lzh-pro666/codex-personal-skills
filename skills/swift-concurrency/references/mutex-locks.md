# Mutex and OSAllocatedUnfairLock

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Mutex

**Module:** `Synchronization` · **Availability:** iOS 18.0+

`Mutex<Value>` is a synchronization primitive that protects shared mutable
state via mutual exclusion. It blocks threads attempting to acquire the lock,
ensuring only one execution context accesses the protected value at a time.

**Documentation:**
[Apple `Mutex`](https://developer.apple.com/documentation/synchronization/mutex)

### Basic Usage

```swift
import Synchronization

class ImageCache: Sendable {
    let storage = Mutex<[String: UIImage]>([:])

    func image(forKey key: String) -> UIImage? {
        storage.withLock { $0[key] }
    }

    func store(_ image: UIImage, forKey key: String) {
        storage.withLock { $0[key] = image }
    }

    func removeAll() {
        storage.withLock { $0.removeAll() }
    }
}
```

### withLockIfAvailable

Use `withLockIfAvailable` to attempt acquisition without blocking. Returns
`nil` if the lock is already held.

```swift
let counter = Mutex<Int>(0)

// Non-blocking attempt — returns nil if lock is contended
if let value = counter.withLockIfAvailable({ $0 }) {
    print("Current count: \(value)")
} else {
    print("Lock was busy, skipping")
}
```

### Key Properties

- **Generic over `Value`:** The protected state is stored inside the mutex,
  making it clear what the lock protects.
- **`Sendable`:** `Mutex` conforms to `Sendable`, so it can be stored in
  `Sendable` types (classes, actors, global state).
- **Non-recursive:** Attempting to lock a `Mutex` that you already hold on the
  same thread is undefined behavior.
- **Synchronous only:** Do not `await` inside `withLock`. The lock is held for
  the duration of the closure — blocking across a suspension point will
  deadlock or starve other threads.

## OSAllocatedUnfairLock

**Module:** `os` · **Availability:** iOS 16.0+

`OSAllocatedUnfairLock<State>` wraps `os_unfair_lock` in a safe Swift API.
It heap-allocates the underlying lock, avoiding the unsound address-of
problem that makes raw `os_unfair_lock` unusable from Swift.

**Documentation:**
[Apple `OSAllocatedUnfairLock`](https://developer.apple.com/documentation/os/osallocatedunfairlock)

### State-Protecting Lock

```swift
import os

enum LoadState: Sendable {
    case idle
    case loading
    case complete(Data)
    case failed(Error)
}

final class ResourceLoader: Sendable {
    let state = OSAllocatedUnfairLock(initialState: LoadState.idle)

    func beginLoading() {
        state.withLock { $0 = .loading }
    }

    func completeLoading(with data: Data) {
        state.withLock { $0 = .complete(data) }
    }

    var currentState: LoadState {
        state.withLock { $0 }
    }
}
```

### Stateless Lock

When protecting external state or a code section rather than a specific value:

```swift
let lock = OSAllocatedUnfairLock()

lock.withLock {
    // Critical section — no associated state
    writeToSharedFile(data)
}
```

### Manual lock/unlock

Available but discouraged. Must unlock from the same thread that locked.
**Never** use across `await` suspension points.

```swift
lock.lock()
defer { lock.unlock() }
// Critical section
```

### Mutex vs OSAllocatedUnfairLock

| | `Mutex<Value>` | `OSAllocatedUnfairLock<State>` |
|---|---|---|
| **Availability** | iOS 18+ | iOS 16+ |
| **Module** | `Synchronization` | `os` |
| **State model** | Value stored inside lock (generic `Value`) | Optional state via `initialState:` |
| **`withLockIfAvailable`** | Returns `nil` on contention | Returns `nil` on contention |
| **Ownership assertions** | Not available | `precondition(.owner)` / `precondition(.notOwner)` |
| **Manual lock/unlock** | Not available | Available (`lock()` / `unlock()`) |
| **Recommendation** | Preferred for iOS 18+ code | Use when targeting iOS 16–17 |

**Guideline:** Use `Mutex` for new code targeting iOS 18+. For apps that run on
iOS 16 through current releases, either keep the shared abstraction backed by
`OSAllocatedUnfairLock` or branch with `#available(iOS 18, *)` so iOS 18+ uses
`Mutex` and iOS 16–17 uses `OSAllocatedUnfairLock`. Prefer
`OSAllocatedUnfairLock` when you need ownership assertions for debugging.
Do not introduce a broad generic lock wrapper with `@unchecked Sendable` just to
hide the deployment-target branch; keep the protected state inside the concrete
primitive. If a legacy wrapper truly needs `@unchecked Sendable`, document the
invariant: all mutable state is private, every access uses the same lock, no
mutable references escape the wrapper, and no lock is held across `await`.

When showing an availability branch, use runtime availability and concrete
implementations. Do not use `#if swift(...)`, `#if os(...)`, or Catalyst checks
as substitutes for API availability:

```swift
protocol MetricsStore: Sendable {
    func increment(_ key: String)
}

func makeMetricsStore() -> any MetricsStore {
    if #available(iOS 18, *) {
        return MutexMetricsStore()
    } else {
        return UnfairLockMetricsStore()
    }
}
```
