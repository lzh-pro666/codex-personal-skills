---
name: swiftui-uikit-interop
description: Implement or review SwiftUI–UIKit boundaries using representables, coordinators, UIHostingController, UIHostingConfiguration, or shared observable state. Use when wrapping UIKit in SwiftUI, embedding SwiftUI in UIKit, or diagnosing lifecycle, sizing, state-sync, delegate, and dismissal bugs at that boundary.
---

# SwiftUI–UIKit Interop

Keep ownership, lifecycle, layout, and state flow explicit across the framework boundary. Confirm the affected target's iOS and Swift versions; in siuper-ios, default to iOS 17 compatibility.

## Workflow

1. Determine which framework owns the screen, state, navigation, and layout.
2. Inspect the complete wrapper/host plus its call sites and delegate callbacks.
3. Choose the narrowest bridge: `UIViewRepresentable`, `UIViewControllerRepresentable`, `UIHostingController`, or `UIHostingConfiguration`.
4. Define state direction explicitly: binding for two-way values, closures/delegates for events, observable models for shared state.
5. Verify repeated updates, dismissal, cleanup, sizing, actor isolation, and backward deployment behavior.

## Core Rules

- Create UIKit objects in `make*`; synchronize changed inputs in `update*` with equality/reentrancy guards.
- Set long-lived delegates once and refresh copied coordinator inputs when value-type wrapper state changes.
- Clean up observers, tasks, timers, delegates, and retained callbacks in the appropriate dismantle or lifecycle path.
- Let SwiftUI own the represented view's outer geometry. Use intrinsic sizing, `sizeThatFits`, constraints, or internal UIKit layout instead of mutating the wrapper's frame during updates.
- Use complete UIKit child containment when embedding `UIHostingController`.
- Handle success, cancellation, error, and dismissal consistently for presented controllers.
- Keep UIKit work on the main actor, but do not introduce newer observation or concurrency APIs without checking the target.
- Treat automatic UIKit observation as version-sensitive; preserve explicit callbacks/Combine where required by the deployment target.

## Load References Only When Needed

- Specialized wrappers for web views, pickers, share/mail/document/PDF surfaces, or unusual text-view behavior: `references/representable-recipes.md`
- Large-scale UIKit-to-SwiftUI migration, advanced sizing/navigation, or versioned UIKit observation: `references/hosting-migration.md`

The core rules above cover ordinary coordinators, update guards, containment, cleanup, and dismissal. Do not load a reference for those routine cases.

## Completion Check

- There is one clear owner for state and presentation.
- Repeated `update*` calls cannot loop, duplicate work, or reset user state.
- Cleanup and every delegate exit path are covered.
- Layout works under the actual container and deployment target.
- Targeted build/tests pass, or the exact verification gap is reported.
