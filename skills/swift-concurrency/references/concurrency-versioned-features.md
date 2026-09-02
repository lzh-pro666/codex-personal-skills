# Versioned Concurrency Features

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## SE-0472: Task.immediate

`Task.immediate` starts executing synchronously on the current actor before any
suspension point, rather than being enqueued. There is also
`Task.immediateDetached` which combines immediate start with detached semantics.

```swift
Task.immediate { await handleUserInput() }
```

Use for latency-sensitive work where enqueue delay is unacceptable.

## Swift 6.4 Cleanup APIs

Swift 6.4 introduces async `defer` (SE-0493) and cancellation shields (SE-0504).
Use them only when the installed toolchain implements the feature and the target meets
the platform availability of `withTaskCancellationShield`.

Use async `defer` when cleanup itself must call async APIs. The defer body
inherits surrounding isolation and is implicitly awaited at scope exit, but it
does not hide cancellation from cleanup code.

Use `withTaskCancellationShield` only for short cleanup or rollback that must
finish after cancellation. Do not wrap normal user-cancelable work in a shield.

## Isolated Conformances

A conformance that needs MainActor state is called an *isolated conformance*.
The compiler ensures the conformance is only used in a matching isolation
context.

```swift
protocol Exportable {
    func export()
}

extension StickerModel: @MainActor Exportable {
    func export() { photoProcessor.exportAsPNG() }
}

@MainActor
struct ImageExporter {
    var items: [any Exportable]

    mutating func add(_ item: StickerModel) {
        items.append(item)  // OK -- on MainActor
    }
}

// But in a nonisolated context:
nonisolated struct GenericExporter {
    var items: [any Exportable]

    mutating func add(_ item: StickerModel) {
        // Error: Main actor-isolated conformance of 'StickerModel' to
        // 'Exportable' cannot be used in nonisolated context
        items.append(item)
    }
}
```

## SE-0481: weak let

Immutable weak references (`weak let`) enable `Sendable` conformance for types
that hold weak references, since immutability guarantees thread safety.
SE-0481 is implemented in Swift 6.3.

## SE-0475: Transactional Observation (Observations)

`Observations { }` provides transactional observation of `@Observable` types
via `AsyncSequence`.

```swift
for await _ in Observations { model.count } {
    print("Count changed to \(model.count)")
}
```
