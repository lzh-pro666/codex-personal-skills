# Approachable Concurrency Examples

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Core Problem Solved

In Swift 6.0/6.1, data-race safety was enforced at compile time, but the most
natural code to write often produced data-race errors. Async functions on types
with mutable state would implicitly hop to the global concurrent executor,
causing send-safety violations even when no actual parallelism was intended.

```swift
// Swift 6.0/6.1: This produces a data-race error
class PhotoProcessor {
    func extractSticker(data: Data, with id: String?) async -> Sticker? { /* ... */ }
}

@MainActor
final class StickerModel {
    let photoProcessor = PhotoProcessor()

    func extractSticker(_ item: PhotosPickerItem) async throws -> Sticker? {
        guard let data = try await item.loadTransferable(type: Data.self) else { return nil }
        // Error: Sending 'self.photoProcessor' risks causing data races
        return await photoProcessor.extractSticker(data: data, with: item.itemIdentifier)
    }
}
```

```swift
// Swift 6.2: The same code compiles without error
// because extractSticker stays on the caller's actor
class PhotoProcessor {
    func extractSticker(data: Data, with id: String?) async -> Sticker? { /* ... */ }
}

@MainActor
final class StickerModel {
    let photoProcessor = PhotoProcessor()

    func extractSticker(_ item: PhotosPickerItem) async throws -> Sticker? {
        guard let data = try await item.loadTransferable(type: Data.self) else { return nil }
        return await photoProcessor.extractSticker(data: data, with: item.itemIdentifier)
    }
}
```

## SE-0466: Default MainActor Isolation

Enable with the `-default-isolation MainActor` compiler flag, SwiftPM
`.defaultIsolation(MainActor.self)`, or Xcode's separate `Default Actor
Isolation` build setting set to `MainActor`.

Do not confuse this with Xcode's `Approachable Concurrency` build setting, which
enables a bundle of upcoming-feature flags such as nonisolated-nonsending by
default, isolated-conformance inference, inferred Sendable captures, and related
global-actor usability changes.

**What it does:**
- Unannotated declarations in the module are inferred as `@MainActor` unless
  opted out.
- Global and static variables are protected by the main actor by default.
- Protocol conformances are implicitly isolated to `@MainActor`.
- Eliminates most annotation burden for single-threaded UI code.

**Recommended for:** Apps, scripts, and executable targets. Not recommended for
library targets that should remain actor-agnostic.

```swift
// With default MainActor isolation -- no @MainActor annotations needed:
final class StickerLibrary {
    static let shared = StickerLibrary()
}

final class StickerModel {
    let photoProcessor = PhotoProcessor()
    var selection: [PhotosPickerItem] = []
}

extension StickerModel: Exportable {
    func export() { photoProcessor.exportAsPNG() }
}
```

## SE-0461: nonisolated(nonsending)

Nonisolated async functions stay on the caller's actor by default instead of
hopping to the global concurrent executor. This is the `nonisolated(nonsending)`
default behavior.

**Key implication:** Values passed into an async function are never sent outside
the actor, eliminating data races without annotation.

To explicitly opt into background execution, use `@concurrent`.

## `@concurrent` Attribute

Ensures a function always runs on the concurrent thread pool, freeing the
calling actor for other work.

```swift
class PhotoProcessor {
    var cachedStickers: [String: Sticker] = [:]

    func extractSticker(data: Data, with id: String) async -> Sticker {
        if let sticker = cachedStickers[id] { return sticker }
        let sticker = await Self.extractSubject(from: data)
        cachedStickers[id] = sticker
        return sticker
    }

    @concurrent
    static func extractSubject(from data: Data) async -> Sticker { /* ... */ }
}
```

**Steps to offload a function to background:**
1. Ensure the containing type is `nonisolated` or the function can be called
   from a nonisolated context.
2. Add `@concurrent` to the function. `nonisolated` alone does not move
   CPU-heavy work off the caller's actor.
3. Add `async` if not already asynchronous.
4. Add `await` at call sites.

```swift
nonisolated struct PhotoProcessor {
    @concurrent
    func process(data: Data) async -> ProcessedPhoto? { /* ... */ }
}

processedPhotos[item.id] = await PhotoProcessor().process(data: data)
```
