# Synchronization Primitive Router

Choose the ownership model before loading implementation details:

- Mutex and OSAllocatedUnfairLock APIs, availability, and lock-backed examples: [mutex-locks.md](mutex-locks.md)
- Atomic counters, flags, compare-and-swap, and memory ordering: [atomics.md](atomics.md)
- Actor-versus-lock decisions and anti-patterns: [synchronization-selection.md](synchronization-selection.md)

Read only the selected primitive reference. Never hold a synchronous lock across an await.
