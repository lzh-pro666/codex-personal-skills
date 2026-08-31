# Siuper Android Conventions

Read this reference for cross-module changes, nontrivial state/Flow behavior, hybrid Compose/View work, or test selection. Repository code and the current `AGENTS.md` remain authoritative when they differ from this snapshot.

## Observed Project Shape

At the time this skill was authored, `siuper-sdk-android` is a multi-module SDK and business UI repository:

```text
foundation/common
        ↓
siuper-model / sdk-api / service-api / network
        ↓
siuper-service / siuper-sdk
        ↓
business modules
        ↓
SampleApp
```

This diagram is directional guidance, not a complete Gradle graph. Confirm real dependencies in `settings.gradle.kts` and each affected `build.gradle.kts`.

The project currently mixes Fragments, custom Views, Jetpack Compose, Room, gRPC, manager APIs, and service interfaces. It does not use Hilt annotations in the inspected source, even though Hilt coordinates exist in the version catalog. Do not introduce Hilt merely because the dependency is listed.

## API and Service Boundaries

- `siuper-sdk-api` contains host-facing manager interfaces and shared API models.
- `siuper-service-api` contains service interfaces used across implementation boundaries.
- `SiuperManager` is the established entry point for many business-layer managers.
- `ServiceManager` supports global and user-scoped services. Preserve the scope distinction and clearing behavior when changing registration or lookup.
- Room DAOs and network implementations should remain behind their owning layer unless nearby architecture explicitly exposes them to the same business module.

Do not add a generic repository or use-case layer solely to match textbook MVVM. Existing code often calls manager interfaces from ViewModels; preserve that boundary unless the requested change demonstrates a policy/orchestration object with a stable responsibility.

## BaseViewModel Contract

`foundation/common` defines `BaseViewModel<S : UiState, E : UiEvent, F : UiEffect>` with:

- a private `MutableStateFlow` exposed as read-only `StateFlow`;
- buffered `MutableSharedFlow` values for events and effects;
- event handling inside `viewModelScope`;
- `setState`/`updateState` reducer helpers;
- `sendEffect` for transient output.

Before changing those buffers or converting an effect to state, answer:

1. Must a value survive collector absence or recreation?
2. May repeated equal values be conflated?
3. Is delivery broadcast or point-to-point?
4. What happens when the buffer is full?
5. Which lifecycle owns production and collection?

Screen code not based on `BaseViewModel` should follow its own established contract; do not migrate it incidentally.

## Lifecycle and Flow Patterns

For Fragment View collection, bind to the View rather than the Fragment object:

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        launch { viewModel.uiState.collect(::render) }
        launch { viewModel.effect.collect(::handleEffect) }
    }
}
```

Use separate children when both flows must collect concurrently. Cancellation at `onDestroyView` prevents collectors from retaining dead bindings or rendering into a destroyed View.

For Compose render state, prefer `collectAsStateWithLifecycle` where the module already provides the lifecycle Compose dependency. Use plain `collectAsState` only when the non-lifecycle-aware lifetime is deliberate and verified.

Treat effect delivery carefully: collecting a replay-0 `SharedFlow` as state can obscure one-shot semantics. Follow the affected screen's established handling or correct it with an explicit explanation and regression test.

## Coroutine Decisions

- Keep job ownership visible. A job stored in a ViewModel must be cancelled/replaced according to the user action or data identity it represents.
- Preserve cancellation through broad exception handlers. Re-throw `CancellationException` when it can be intercepted.
- Use `runTest` virtual time for debounce, retry, polling, and timeout behavior. Coordinate test dispatchers through one scheduler.
- `StandardTestDispatcher` is the repository's normal Main test dispatcher. Use `UnconfinedTestDispatcher` only for intentionally eager entry.
- Avoid hard-coded dispatcher changes unless the operation is actually blocking/CPU-bound or test control requires an injected boundary.

## Hybrid UI Decisions

### Compose inside Fragment/View

Set the `ViewCompositionStrategy` before `setContent`. For Fragment View ownership, nearby code uses:

```kotlin
setViewCompositionStrategy(
    ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed,
)
```

Do not copy this to RecyclerView pooling, Activity-only, or dialog-owned containers without checking their real lifetime.

### View inside Compose

Create the View in `AndroidView.factory`. Update changing values and callbacks in `update` without adding duplicate listeners. If updating a View property invokes the callback that mutates Compose state, compare values or suppress only that programmatic callback to prevent a loop.

Use `DisposableEffect` for composition-owned overlays, listeners, observers, or resources and ensure the key identifies the registered object. Do not retain Activity/Fragment Context in a singleton or ViewModel.

## Tests and Commands

Inspect module dependencies before selecting a layer:

- JUnit: pure Kotlin, state reducers, managers with fakes/mocks, parsers, schedulers.
- JUnit + `kotlinx-coroutines-test`: cancellation, Flow, debounce, retry, job replacement.
- Robolectric: Android resources, Views, lifecycle, and loopers when its model is faithful.
- Instrumentation/device: real window/IME, platform service, accessibility, camera/media, rendering, or vendor integration.

Typical focused command:

```bash
./gradlew :business:siuper-chat:testDebugUnitTest \
  --tests 'com.siuper.chat.search.ChatSearchRequestSchedulerTest'
```

Use the exact module and fully qualified test class. Run the nearby suite when shared global state, manager registration, Room, or lifecycle interaction creates a credible integration risk.

The root `AGENTS.md` currently requires specialized commands for Vector Drawable edits and density-preserving Coil circle crop changes. Re-read it at task time; do not duplicate its exact rules here because project instructions may evolve.

## Version and Source Lookup

Read the version catalog and module Gradle file before using an API. Use primary Android documentation for platform and Jetpack behavior, primary Kotlin documentation for language and Gradle questions, and the installed official task Skills only for their named surfaces. Third-party behavior must be checked against the project's pinned version and the library's official documentation, release notes, or source. Do not infer that the latest documentation applies to the pinned dependency.

Useful official starting points:

- [Android skills](https://developer.android.com/tools/agents/android-skills/browse)
- [Android coroutine best practices](https://developer.android.com/kotlin/coroutines/coroutines-best-practices)
- [Lifecycle-aware Flow collection](https://developer.android.com/topic/libraries/architecture/views/coroutines-views)
- [`kotlinx-coroutines-test`](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/)
