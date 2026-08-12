---
name: ios-accessibility
description: Implement or review accessibility in iOS UIKit or SwiftUI interfaces. Use for VoiceOver, Voice Control, Switch Control, Full Keyboard Access, labels/traits/actions, traversal and focus, Dynamic Type, reduced motion/contrast, media accessibility, accessibility tests, or App Store accessibility claims.
---

# iOS Accessibility

Make the changed user flow operable and understandable with relevant assistive technologies. Scope the audit to reachable behavior unless the user requests a product-wide compliance review.

## Workflow

1. Identify the user task, affected controls, framework, and minimum deployment target.
2. Inspect semantic elements, labels, values, traits, actions, grouping, traversal order, focus transitions, hit targets, and Dynamic Type behavior.
3. Check non-touch alternatives for gestures and system preferences relevant to the change.
4. Prefer native controls and visible text semantics before adding custom accessibility overrides.
5. Verify with focused automated checks where possible and state which manual assistive-technology checks remain.

## Core Rules

- Add labels only when visible text or native control semantics do not already provide a correct accessible name.
- Keep labels concise and omit control types already announced by traits. Expose state through values/traits rather than embedding it ambiguously in labels.
- Hide only truly decorative content. Preserve meaningful images, charts, status, and user-generated content.
- Give gesture-only actions an accessible action or equivalent control; keep interactive targets reachable and at least 44×44 points where applicable.
- Group elements only when the combined element still exposes every required action and value. Verify traversal order rather than assuming visual order.
- Restore accessibility focus after modal or destructive transitions when the default behavior is insufficient.
- Support Dynamic Type and avoid conveying information by color alone. Respect reduced-motion and contrast preferences when the UI uses those effects.
- Do not claim App Store accessibility support from code inspection alone; require evidence across common tasks and relevant device types.

## Load References Only When Needed

- Custom controls, adjustable actions, focus restoration, complex grouping/traversal, rotors, or advanced accessibility tests: `references/a11y-patterns.md`
- Captions, audio descriptions, and media characteristics: `references/media-accessibility.md`
- App Store Accessibility Nutrition Labels or App Store Connect claims: `references/nutrition-labels.md`

Native control labels, traits, hit targets, and basic Dynamic Type checks are covered above and need no reference. Read only the specialized reference matching the requested surface.

## Completion Check

- The affected task is reachable, labeled, actionable, and ordered correctly.
- State changes and errors are perceivable without relying only on color, motion, or position.
- Dynamic Type and relevant accessibility preferences are handled.
- Automated and manual verification are distinguished; unperformed device checks are not presented as passed.
