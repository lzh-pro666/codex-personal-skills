# Accessibility Alternative Input

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Voice Control Patterns

Voice Control generates tap targets from accessibility labels. Labels must be speakable and unique within the visible screen.

### accessibilityInputLabels (iOS 14+)

Provide shorter spoken alternatives when the primary label is long, awkward, repeated, localized, acronym-heavy, or commonly shortened in speech:

```swift
// Primary label is descriptive but long to speak
Button(action: { startWorkout() }) {
    VStack {
        Image(systemName: "figure.run")
        Text("Start Outdoor Running Workout")
    }
}
.accessibilityLabel("Start Outdoor Running Workout")
.accessibilityInputLabels(["Start Run", "Run", "Start Workout"])
```

```swift
// Navigation link with verbose label
NavigationLink {
    AccountSettingsView()
} label: {
    Label("Account and Privacy Settings", systemImage: "person.circle")
}
.accessibilityInputLabels(["Account", "Settings", "Privacy"])
```

Also consider input labels for repeated row actions, quantity controls, media controls, and product-name labels where Voice Control users are likely to speak a shorter command than the visible text.

### Speakable Label Guidelines

```swift
// Bad: emoji-only, unspeakable
Button("❤️") { toggleFavorite() }

// Good: speakable label
Button(action: { toggleFavorite() }) {
    Image(systemName: "heart.fill")
}
.accessibilityLabel("Favorite")

// Bad: duplicate labels on same screen
ForEach(items) { item in
    Button("Edit") { edit(item) }  // Voice Control can't distinguish
}

// Good: unique labels
ForEach(items) { item in
    Button("Edit") { edit(item) }
        .accessibilityLabel("Edit \(item.name)")
}
```

## Switch Control Patterns

Switch Control scans elements sequentially. Reduce scan stops with grouping and provide custom actions for gesture-based interactions.

### Custom Actions for Gesture Alternatives

```swift
// Swipe-to-delete row: Switch Control can't swipe
TaskRow(task: task)
    .accessibilityAction(named: "Complete") { completeTask(task) }
    .accessibilityAction(named: "Delete") { deleteTask(task) }
    .accessibilityAction(named: "Reschedule") { rescheduleTask(task) }
```

```swift
// Long-press context menu: expose actions directly
PhotoThumbnail(photo: photo)
    .contextMenu { /* ... */ }
    .accessibilityAction(named: "Share") { sharePhoto(photo) }
    .accessibilityAction(named: "Add to Album") { addToAlbum(photo) }
    .accessibilityAction(named: "Delete") { deletePhoto(photo) }
```

### Grouping for Scan Efficiency

```swift
// Bad: 5 scan stops per row
HStack {
    Image(systemName: "doc")
    VStack {
        Text(document.title)
        Text(document.date.formatted())
    }
    Spacer()
    Text(document.size)
    Image(systemName: "chevron.right")
}

// Good: 1 scan stop per row
HStack {
    Image(systemName: "doc")
    VStack {
        Text(document.title)
        Text(document.date.formatted())
    }
    Spacer()
    Text(document.size)
    Image(systemName: "chevron.right")
}
.accessibilityElement(children: .combine)
```

## Full Keyboard Access Patterns

Full Keyboard Access review checks whether keyboard users can complete the same common tasks without touch. Keep the implementation mechanics in the `focus-engine` skill when the fix requires Tab-order wiring, skipped custom cards, `.focusable()`, SwiftUI keyboard focus state, focus sections, directional movement, tvOS focus, or `UIFocusGuide`.

- Every interactive control is reachable by keyboard.
- Activation works with expected keyboard input.
- Focus indicators are visible and not hidden by custom styling.
- Focus traversal is logical and does not trap users in a region.
- Gesture-only interactions have keyboard-operable alternatives.
- App shortcuts do not override system shortcuts.
- Custom controls skipped by Tab should be filed as keyboard focus implementation issues and routed to `focus-engine`; keep the accessibility finding here.
- Explicitly assess traversal impact: accessibility element order and grouping affect VoiceOver swipe order, Switch Control scan order, Voice Control overlay targeting, and Full Keyboard Access reachability review.
