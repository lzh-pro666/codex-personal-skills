# Accessibility Semantics, Focus, and Layout

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Labels, Values, and Hints

```swift
Button(action: { }) {
    Image(systemName: "heart.fill")
}
.accessibilityLabel("Favorite")

Slider(value: $volume, in: 0...100)
    .accessibilityValue("\(Int(volume)) percent")

Button("Submit")
    .accessibilityHint("Submits the form and sends your feedback")
```

## Traits and Element Grouping

```swift
// Add traits without overwriting defaults
Button("Go") { }
    .accessibilityAddTraits(.updatesFrequently)

// Group children into a single accessibility element
HStack {
    Image(systemName: "person.circle")
    VStack {
        Text("John Doe")
        Text("Engineer")
    }
}
.accessibilityElement(children: .combine)

// Binary custom control: prefer Toggle when possible; otherwise expose toggle state
HStack {
    Image(systemName: isFavorite ? "heart.fill" : "heart")
    Text(product.name)
}
.onTapGesture { isFavorite.toggle() }
.accessibilityElement()
.accessibilityLabel("Favorite \(product.name)")
.accessibilityValue(isFavorite ? "On" : "Off")
.accessibilityAddTraits(.isToggle)
.accessibilityAction { isFavorite.toggle() }
```

## Custom Controls and Adjustable Actions

```swift
HStack { /* custom star rating UI */ }
    .accessibilityElement()
    .accessibilityLabel("Rating")
    .accessibilityValue("\(rating) out of 5 stars")
    .accessibilityAdjustableAction { direction in
        switch direction {
        case .increment: if rating < 5 { rating += 1 }
        case .decrement: if rating > 1 { rating -= 1 }
        @unknown default: break
        }
    }
```

For custom quantity controls, steppers, ratings, sliders, or other adjustable values, prefer the native control first. If the control is custom, SwiftUI needs `.accessibilityAdjustableAction`; UIKit custom controls also need `accessibilityTraits.insert(.adjustable)`.

## Focus Management Patterns

```swift
@AccessibilityFocusState private var focusOnTrigger: Bool

Button("Open Settings") { showSheet = true }
    .accessibilityFocused($focusOnTrigger)
    .sheet(isPresented: $showSheet) {
        SettingsSheet()
            .onDisappear {
                focusOnTrigger = true
            }
    }
```

```swift
enum A11yFocus: Hashable { case nameField, emailField, submitButton }
@AccessibilityFocusState private var focus: A11yFocus?
```

## Dynamic Type and Layout

```swift
@ScaledMetric(relativeTo: .title) private var iconSize: CGFloat = 24
@ScaledMetric(relativeTo: .body) private var rowSpacing: CGFloat = 12
@ScaledMetric(relativeTo: .body) private var controlHeight: CGFloat = 44
@Environment(\.dynamicTypeSize) var dynamicTypeSize

var body: some View {
    Group {
        if dynamicTypeSize.isAccessibilitySize {
            VStack(alignment: .leading) { icon; textContent }
        } else {
            HStack { icon; textContent }
        }
    }
    .frame(minHeight: controlHeight)
}
```

Use `@ScaledMetric(relativeTo:)` for non-text dimensions that need to track text size, including icon sizes, spacing, control heights, and custom hit-region dimensions.

## Custom Rotors

```swift
List(items) { item in ItemRow(item: item) }
    .accessibilityRotor("Unread") {
        ForEach(items.filter { !$0.isRead }) { item in
            AccessibilityRotorEntry(item.title, id: item.id)
        }
    }
```

## System Accessibility Preferences

```swift
@Environment(\.accessibilityReduceMotion) var reduceMotion
@Environment(\.accessibilityReduceTransparency) var reduceTransparency
@Environment(\.colorSchemeContrast) var contrast
@Environment(\.legibilityWeight) var legibilityWeight
```

## UIKit Accessibility Patterns

```swift
customButton.accessibilityTraits.insert(.button)
customButton.accessibilityTraits.remove(.staticText)

UIAccessibility.post(notification: .announcement, argument: "Upload complete")
UIAccessibility.post(notification: .layoutChanged, argument: targetView)
UIAccessibility.post(notification: .screenChanged, argument: newScreenView)
```

## Common Mistakes Checklist

- Direct trait assignment instead of `.accessibilityAddTraits`
- Missing focus restoration after dismissing sheets
- Ungrouped list rows creating excessive swipe stops
- Icon-only buttons missing labels
- Ignoring Reduce Motion, Reduce Transparency, or Increase Contrast
- Fixed font sizes that break Dynamic Type
- Tap targets smaller than 44x44 points
