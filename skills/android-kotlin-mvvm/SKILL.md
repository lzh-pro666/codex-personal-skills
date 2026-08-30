---
name: android-kotlin-mvvm
description: Design, implement, review, or explicitly validate Android/Kotlin changes in siuper-sdk-android while preserving its module boundaries, manager APIs, StateFlow-based ViewModel conventions, coroutine lifecycles, mixed Compose/View UI, and focused Gradle tests. Do not invoke merely because an Obsidian note records Android work; use official Android/Kotlin guidance separately for generic platform or tooling questions.
---

# Android Kotlin MVVM

Keep Android changes consistent with the architecture already present in `siuper-sdk-android`. This is a project-convention skill, not a generic Android manual and not authority to migrate frameworks or redesign unrelated modules.

## Authority and Routing

1. Treat the user's request, repository `AGENTS.md`, Gradle configuration, nearby production code, and tests as the authority for project behavior and compatibility.
2. Identify the owning layer, public interface, state owner, lifecycle owner, and narrowest Gradle module affected before editing.
3. Preserve sound local conventions. If nearby code conflicts with a repository rule or requested behavior, call out the conflict instead of copying it.
4. Verify the actual Kotlin, AGP, Compose, AndroidX, coroutines, compileSdk, minSdk, and pinned third-party versions before using version-sensitive APIs. Use primary Android, Kotlin, or library documentation for facts that the repository cannot answer; never guess an API or upgrade a dependency implicitly.
5. Load an installed official Android task Skill alongside this project Skill only for its matching surface:
   - `$edge-to-edge` for Compose system bars, insets, or IME overlap;
   - `$android-intent-security` for components, Intents, PendingIntents, providers, receivers, or exported surfaces;
   - `$r8-analyzer` for R8 or Proguard configuration analysis.
6. A task Skill does not authorize an unrelated UI migration, SDK/dependency upgrade, framework introduction, test, build, project command, or code mutation. The user's requested outcome and repository constraints still define scope.

## Project Boundaries

- Keep public SDK contracts in `siuper-sdk-api` or the established API module; service contracts belong in `siuper-service-api`; implementations stay behind those interfaces.
- Business UI should prefer the established `SiuperManager` or service/API boundary. Do not make a Fragment or composable reach directly into gRPC, Room internals, or another module's implementation detail when an existing manager owns that operation.
- Do not impose a generic `UI → UseCase → Repository` stack when the feature already uses manager/service boundaries. Introduce a repository, coordinator, or use case only when it owns meaningful policy, orchestration, reuse, or a test seam.
- Respect Gradle dependency direction. Do not solve a dependency problem by importing a higher-level business module into a lower-level foundation, model, API, or service module.

## ViewModel and State

- For flows using `BaseViewModel<S, E, F>`, keep durable render state in `StateFlow`, user inputs as `UiEvent`, and transient UI work as `UiEffect` only when the existing screen follows that contract.
- Update state through the existing reducer helpers and model state transitions explicitly. Do not expose mutable flows or let the UI mutate ViewModel-owned collections.
- A ViewModel may hold application-safe managers, services, DAOs, and immutable data; it must not retain an Activity, Fragment, View, binding, short-lived Context, or navigation controller.
- Preserve one owner for each state value. Avoid mirroring durable state independently in the View, Compose, and ViewModel layers.

## Coroutines and Flow

- Use `viewModelScope` for ViewModel-owned work. UI collection in a Fragment must follow `viewLifecycleOwner`; visibility-sensitive collectors should use `repeatOnLifecycle`.
- In Compose, prefer lifecycle-aware collection for screen state. Give `LaunchedEffect` and `DisposableEffect` keys that match the real resource lifetime and clean up listeners, overlays, tasks, and callbacks.
- Avoid `GlobalScope`, unmanaged `CoroutineScope`, real sleeps as synchronization, blocking the main thread, and swallowing `CancellationException`.
- Before changing `StateFlow`, `SharedFlow`, channel, buffering, replay, debounce, or `shareIn` behavior, state the delivery contract: subscriber absence, restart, ordering, overflow, cancellation, and error propagation.
- When multiple flows are collected inside `repeatOnLifecycle`, launch sibling children if they must run concurrently; sequential `collect` calls do not progress together.

## Compose and Views

- Treat the codebase as hybrid. Do not migrate a whole View/Fragment screen to Compose, or Compose back to Views, unless the user requests that migration.
- Fragment-hosted `ComposeView` must use a composition-disposal strategy that matches the Fragment View lifecycle; existing project code commonly uses `DisposeOnViewTreeLifecycleDestroyed`.
- Create embedded Views in `AndroidView.factory`; make `update` idempotent and guard feedback loops when programmatic updates trigger callbacks.
- Keep outer geometry owned by the parent toolkit, release boundary resources, and verify focus, IME, saved state, and accessibility when the change crosses toolkits.

## Testing and Verification

- A standalone note or documentation request authorizes inspection of code, tests, and existing reports only. Do not run Gradle, `adb`, an emulator, or a device check unless the user explicitly asks to verify the implementation or run tests in the current request; record absent execution evidence as `待验证`.
- Prefer local JUnit tests for pure logic and coroutine/Flow behavior; use the module's existing Robolectric setup for Android resource/View behavior it models faithfully.
- Preserve the project's existing test and dependency-injection stack. Do not introduce Hilt, a new mocking framework, screenshot framework, or repository-wide coverage tool merely to satisfy a generic testing recipe.
- Use `runTest` and the shared `TestCoroutineScheduler`; follow the module's `MainDispatcherRule` pattern when replacing `Dispatchers.Main`. Prefer virtual time and completion signals over sleeps.
- Use instrumentation or device checks only for behavior that needs real platform, window, service, hardware, rendering, or accessibility fidelity.
- Derive the focused task from the owning module, for example `./gradlew :business:siuper-chat:testDebugUnitTest --tests 'fully.qualified.TestClass'`.
- When multiple Gradle tasks are authorized in the same checkout, prefer one Gradle invocation that lists all compatible tasks. Otherwise run separate invocations serially. Do not launch multiple Gradle processes concurrently against the same checkout unless repository instructions explicitly establish isolated, concurrency-safe Gradle state. This restriction does not override Gradle's own task scheduling inside one invocation.
- When Vector Drawable XML or density-preserving circle crop code is touched, run the exact checks required by the root `AGENTS.md`.
- Do not run `assemble`, `build`, installation, or full-repository Gradle tasks unless the user explicitly requests a build or the repository instruction for the changed surface requires it.

## Load the Reference Only When Needed

Read `references/siuper-android-conventions.md` when the task crosses modules, uses `BaseViewModel`, changes Flow delivery or coroutine scheduling, crosses Compose/View boundaries, or needs a test-layer/command decision.

Ordinary local edits with clear nearby precedent need no reference.

## Completion Check

- The change stays within the owning module and established API/service direction.
- State, coroutine, lifecycle, and UI-toolkit ownership are explicit, with no leaked Android object.
- Observable behavior has focused verification at the cheapest faithful layer.
- Build/device/manual gaps are reported precisely and are not presented as passed.
