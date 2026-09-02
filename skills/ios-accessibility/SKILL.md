---
name: ios-accessibility
description: Implement or review accessibility in iOS UIKit or SwiftUI interfaces. Use for VoiceOver, Voice Control, Switch Control, Full Keyboard Access, semantics, focus, Dynamic Type, reduced motion/contrast, media accessibility, accessibility tests, or App Store accessibility claims.
---

# iOS Accessibility

Make the affected user task operable and understandable with relevant assistive technologies. Limit the audit to reachable behavior unless the user requests product-wide coverage.

## Decisions

- Identify the user task, controls, framework, deployment target, and relevant assistive technologies.
- Prefer native controls and visible-text semantics. Add concise labels only when existing semantics do not provide the accessible name; expose state through values/traits and preserve meaningful images or status.
- Give gesture-only behavior an accessible action or equivalent control. Keep targets reachable and appropriately sized.
- Group elements only when all actions and values remain available; verify traversal and focus after modal, destructive, or asynchronous transitions.
- Support Dynamic Type and avoid relying only on color, motion, or position. Respect relevant reduced-motion and contrast settings.

## References

- Semantics, grouping, custom controls, focus, Dynamic Type, rotors, preferences, or UIKit notifications: `references/a11y-semantics-focus.md`
- Voice Control, Switch Control, or Full Keyboard Access: `references/a11y-alternative-input.md`
- Accessibility automation and manual-test boundaries: `references/a11y-testing.md`
- Captions or audio descriptions: `references/media-accessibility.md`
- App Store accessibility claims: `references/nutrition-labels.md`

Use `references/a11y-patterns.md` only as a router when the request spans several accessibility surfaces. Do not claim App Store support or device behavior from code inspection alone.

Verify the changed task with focused automation where faithful, distinguish manual assistive-technology checks, and report unperformed device coverage.
