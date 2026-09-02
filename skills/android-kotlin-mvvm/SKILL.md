---
name: android-kotlin-mvvm
description: Design, implement, review, or explicitly validate Android/Kotlin changes in siuper-sdk-android while preserving its module, manager API, StateFlow/ViewModel, coroutine-lifecycle, mixed Compose/View, and focused-test conventions. Do not use for generic Android guidance or merely because a note mentions Android.
---

# Android Kotlin MVVM

Keep changes consistent with `siuper-sdk-android`; do not use this skill to impose a generic architecture or migrate unrelated frameworks.

## Decide from repository evidence

- Treat the request, root and local `AGENTS.md`, Gradle configuration, nearby code, and tests as authority. Confirm version-sensitive APIs against pinned versions and primary documentation.
- Identify the owning module, public boundary, state owner, lifecycle owner, and narrowest verification target before editing.
- Load `$edge-to-edge`, `$android-intent-security`, or `$r8-analyzer` only for matching inset/IME, component/Intent security, or R8/Proguard work. These skills do not expand scope or authorization.
- For explicit cross-platform work or a named shared-contract ambiguity, follow `../development-workflow/references/project-locations.md`; otherwise do not inspect the iOS counterpart.

## Project invariants

- Keep host-facing SDK contracts in the established API module and service contracts in `siuper-service-api`; implementations stay behind those interfaces. Business UI should use the existing `SiuperManager`/service boundary instead of gRPC, Room internals, or reverse module dependencies.
- Do not add a repository/use-case layer unless it owns meaningful policy, orchestration, reuse, or a test seam.
- With `BaseViewModel<S, E, F>`, keep durable render state in read-only `StateFlow`, inputs as events, and transient output as effects when the screen follows that contract. Preserve one owner for each state value and never retain short-lived Android UI objects in a ViewModel.
- Before changing Flow replay, buffering, sharing, debounce, or channels, define behavior for absent/restarted subscribers, ordering, overflow, cancellation, and errors.
- Fragment View collection belongs to `viewLifecycleOwner`; visibility-sensitive collectors use `repeatOnLifecycle`. Collect independent flows in sibling children when they must progress concurrently.
- Treat the UI as hybrid. Match `ComposeView` disposal to its actual owner, create embedded Views in `AndroidView.factory`, keep `update` idempotent, guard callback feedback loops, and release boundary resources.

Read `references/siuper-android-conventions.md` only for cross-module boundaries, nontrivial BaseViewModel/Flow behavior, hybrid UI ownership, or test-layer selection.

## Verification

- A documentation-only request permits source and existing-report inspection, not Gradle, `adb`, emulator, or device execution. Record missing execution evidence as `待验证`.
- Prefer local JUnit and `kotlinx-coroutines-test` for pure logic and Flow; use the existing Robolectric setup for faithful Android behavior and device checks only for real platform/window/service/hardware/rendering fidelity.
- Use the shared test scheduler and virtual time instead of sleeps. Preserve the existing DI and test stack.
- Run the narrowest authorized module task. Combine compatible Gradle tasks in one invocation or run them serially; do not start concurrent Gradle processes in the same checkout unless repository instructions establish isolated state.
- Run root-`AGENTS.md` checks for touched Vector Drawables or density-preserving circle crop logic. Do not run `build`, `assemble`, install, or full-repository tasks unless explicitly requested or required by repository instructions.

Finish only when module/API direction, state/lifecycle ownership, focused verification, and remaining build/device gaps are explicit.
