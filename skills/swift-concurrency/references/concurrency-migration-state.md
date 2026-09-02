# Concurrency State and Migration

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Global and Static State

Global and static variables are prone to data races. The most common protection
is `@MainActor`:

```swift
@MainActor
final class StickerLibrary {
    static let shared = StickerLibrary()  // protected by MainActor
}
```

With default MainActor isolation (SE-0466), this annotation is implicit.

## Migration and Build Settings

All approachable concurrency features are opt-in via:
- **Xcode 26:** Swift Compiler > Concurrency section in build settings.
- **SwiftPM:** `swiftSettings` in Package.swift using the `SwiftSetting` API.

For Swift 6 language mode, strict concurrency checking is complete and
data-race diagnostics are errors. Use Targeted or Minimal only as Swift 5
migration settings while preparing code for Swift 6.

Swift 6.2 includes migration tooling to help make necessary code changes
automatically. See swift.org/migration for details.

## Summary

The Swift 6.2 concurrency progression:
1. Start with code that runs on the main actor by default (no data race risk).
2. Async functions run wherever they are called from (still no data race risk).
3. When you need performance, offload specific code with `@concurrent`.
