---
name: swiftui-uikit-interop
description: Implement or review SwiftUI–UIKit boundaries using representables, coordinators, UIHostingController, UIHostingConfiguration, or shared state. Use for lifecycle, sizing, state-sync, delegate, navigation, or dismissal bugs across the boundary.
---

# SwiftUI–UIKit Interop

Keep ownership, lifecycle, layout, and state flow explicit across the framework boundary. Confirm deployment and Swift versions before using versioned observation or sizing APIs.

## Decisions

- Identify which framework owns the screen, state, navigation, presentation, and outer layout; inspect the complete bridge, call sites, and delegate exits.
- Choose the narrowest bridge: representable for one UIKit view/controller, `UIHostingController` for hosted SwiftUI hierarchy, or `UIHostingConfiguration` for supported reusable cells/content.
- Create UIKit objects in `make*`; synchronize inputs in `update*` with equality or reentrancy guards. Set long-lived delegates once and refresh coordinator inputs copied from value-type wrappers.
- Use bindings for two-way values, closures/delegates for events, and observable models for genuinely shared state. Keep one owner for presentation and durable state.
- Clean up observers, tasks, timers, delegates, callbacks, and presented controllers in the matching dismantle/lifecycle path.
- Let the parent toolkit own outer geometry; use intrinsic sizing, constraints, `sizeThatFits`, or internal layout. Apply complete UIKit child containment to `UIHostingController`.

## References

- MapKit or attributed UITextView wrappers: `references/representable-map-text.md`
- Camera preview or PHPicker: `references/representable-media-pickers.md`
- Mail, share sheet, or message composer: `references/representable-system-presenters.md`
- UISearchBar or PDFKit: `references/representable-search-pdf.md`
- Screen migration or child containment: `references/hosting-screen-containment.md`
- Navigation bridging or shared state: `references/hosting-navigation-state.md`
- UIHostingConfiguration or environment propagation: `references/hosting-configuration-environment.md`

Use `references/representable-recipes.md` or `references/hosting-migration.md` only as routers for a mixed request.

Verify repeated updates, feedback loops, dismissal/cancellation/error paths, cleanup, sizing, actor isolation, and backward deployment behavior with the narrowest authorized checks.
