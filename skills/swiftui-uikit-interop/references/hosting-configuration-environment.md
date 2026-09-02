# Hosting Configuration and Environment

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 5. UIHostingConfiguration (iOS 16+)

Render SwiftUI content inside `UICollectionViewCell` and `UITableViewCell` without managing a child `UIHostingController`. This is the preferred approach for cells in a UIKit collection or table view.

### UICollectionView with SwiftUI Cells

```swift
@available(iOS 16.0, *)
func collectionView(
    _ collectionView: UICollectionView,
    cellForItemAt indexPath: IndexPath
) -> UICollectionViewCell {
    let cell = collectionView.dequeueReusableCell(
        withReuseIdentifier: "cell",
        for: indexPath
    )
    let item = dataSource[indexPath.item]

    cell.contentConfiguration = UIHostingConfiguration {
        HStack {
            AsyncImage(url: item.imageURL) { image in
                image.resizable().scaledToFill()
            } placeholder: {
                ProgressView()
            }
            .frame(width: 60, height: 60)
            .clipShape(.rect(cornerRadius: 8))

            VStack(alignment: .leading) {
                Text(item.title).font(.headline)
                Text(item.subtitle).font(.subheadline).foregroundStyle(.secondary)
            }
        }
    }
    .margins(.all, 12)

    return cell
}
```

### UITableView with SwiftUI Cells

```swift
@available(iOS 16.0, *)
func tableView(
    _ tableView: UITableView,
    cellForRowAt indexPath: IndexPath
) -> UITableViewCell {
    let cell = tableView.dequeueReusableCell(withIdentifier: "cell", for: indexPath)
    let item = items[indexPath.row]

    cell.contentConfiguration = UIHostingConfiguration {
        ItemRowView(item: item)
    }

    return cell
}
```

### Self-Sizing

`UIHostingConfiguration` cells self-size automatically. Ensure:
- The table/collection view uses `UICollectionViewCompositionalLayout` with estimated dimensions, or `tableView.rowHeight = UITableView.automaticDimension`.
- The SwiftUI content has defined height (via content or explicit `.frame`).

### Background Customization

```swift
cell.contentConfiguration = UIHostingConfiguration {
    ItemRowView(item: item)
}
.background {
    RoundedRectangle(cornerRadius: 12)
        .fill(.background)
}
.margins(.horizontal, 16)
.minSize(height: 60)
```

### Gotchas

- **Performance.** Each `UIHostingConfiguration` creates a lightweight hosting controller. For very large lists (10,000+ items), profile with Instruments to ensure smooth scrolling.
- **State management.** The SwiftUI content inside `UIHostingConfiguration` is recreated on each cell reuse. Do not store `@State` that needs to persist across reuse -- use the data model instead.
- **Swipe actions.** In list layouts, SwiftUI `.swipeActions` can bridge through `UIHostingConfiguration`. Use UIKit swipe configuration only when the table or collection view integration needs UIKit to own those actions.
- **Environment.** Inject app-specific environment values explicitly in the `UIHostingConfiguration` closure; content created from UIKit does not inherit a surrounding SwiftUI app environment by default.

---

## 6. Environment Bridging

Pass SwiftUI environment values into hosted SwiftUI views from UIKit, and access UIKit traits from SwiftUI.

### Injecting Environment into UIHostingController

```swift
let model = AppState()
let settingsView = SettingsView()
    .environment(model)
    .environment(\.locale, Locale(identifier: "en_US"))

let hostingVC = UIHostingController(rootView: settingsView)
```

Apply environment modifiers to the root view before passing it to the hosting controller. The hosting controller does not support adding environment values after creation (you would need to reassign `rootView`).

### Trait Collection to SwiftUI Environment

`UIHostingController` automatically bridges these UIKit trait collections to SwiftUI environment values:

| UIKit Trait | SwiftUI Environment |
|------------|-------------------|
| `userInterfaceStyle` | `\.colorScheme` |
| `horizontalSizeClass` | `\.horizontalSizeClass` |
| `verticalSizeClass` | `\.verticalSizeClass` |
| `preferredContentSizeCategory` | `\.dynamicTypeSize` |
| `layoutDirection` | `\.layoutDirection` |
| `legibilityWeight` | `\.legibilityWeight` |

These update automatically when the UIKit trait environment changes (device rotation, split view resize, accessibility settings change).

### Custom Environment Values Across the Bridge

Define a custom environment key and set it from UIKit:

```swift
private struct UserRoleKey: EnvironmentKey {
    static let defaultValue: UserRole = .guest
}

extension EnvironmentValues {
    var userRole: UserRole {
        get { self[UserRoleKey.self] }
        set { self[UserRoleKey.self] = newValue }
    }
}

// UIKit side:
let role = authManager.currentRole
let profileView = ProfileView().environment(\.userRole, role)
let hostingVC = UIHostingController(rootView: profileView)

// SwiftUI side:
struct ProfileView: View {
    @Environment(\.userRole) private var role

    var body: some View {
        if role == .admin {
            AdminDashboard()
        } else {
            UserDashboard()
        }
    }
}
```

### Updating Environment After Creation

To change environment values after the hosting controller is created, wrap the root view in a container that takes a binding or observable:

```swift
struct EnvironmentBridge<Content: View>: View {
    let state: AppState  // @Observable
    let content: Content

    var body: some View {
        content
            .environment(state)
            .environment(\.userRole, state.currentRole)
    }
}

// UIKit:
let state = AppState()
let bridge = EnvironmentBridge(state: state, content: SettingsView())
let hostingVC = UIHostingController(rootView: bridge)

// Later: mutating state.currentRole updates the environment automatically
state.currentRole = .admin
```

### Gotchas

- **`@Environment(\.dismiss)` in hosted views.** This works for SwiftUI presentations and navigation contexts. For a `UIHostingController` pushed by UIKit, pass an explicit callback that calls `popViewController(animated:)`; the pushed controller is not inside a SwiftUI `NavigationStack`.
- **Missing environment.** If a SwiftUI view expects an `@Environment` object and it is not provided, the app crashes at runtime. Always set required environment values before creating the hosting controller.
- **Overriding traits.** Use `hostingVC.overrideUserInterfaceStyle` to force light/dark mode for a hosted SwiftUI view. This propagates to `\.colorScheme` automatically.
