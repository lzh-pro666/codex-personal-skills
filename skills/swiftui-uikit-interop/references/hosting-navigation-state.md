# Hosting Navigation and Shared State

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 3. Navigation Bridging

Mix UIKit and SwiftUI screens in the same `UINavigationController` stack.

### UIKit Pushing SwiftUI

```swift
// From a UIKit view controller, push a SwiftUI screen
func showProfile(for user: User) {
    let profileView = ProfileView(user: user)
    let hostingVC = UIHostingController(rootView: profileView)
    hostingVC.title = user.name
    navigationController?.pushViewController(hostingVC, animated: true)
}
```

### SwiftUI Pushing UIKit

Use a coordinator or `UIViewControllerRepresentable` bridge:

```swift
struct ProfileView: View {
    let user: User
    @State private var showLegacyEditor = false

    var body: some View {
        List {
            // ... profile content
            Button("Edit (Legacy)") { showLegacyEditor = true }
        }
        .sheet(isPresented: $showLegacyEditor) {
            LegacyEditorWrapper(user: user)
        }
    }
}

struct LegacyEditorWrapper: UIViewControllerRepresentable {
    let user: User

    func makeUIViewController(context: Context) -> UINavigationController {
        let editor = ProfileEditorViewController(user: user)
        return UINavigationController(rootViewController: editor)
    }

    func updateUIViewController(_ uiViewController: UINavigationController, context: Context) {}
}
```

### Passing NavigationController Reference

For deep integration where SwiftUI needs to push onto the UIKit navigation stack:

```swift
struct NavigationBridge {
    weak var navigationController: UINavigationController?

    func push(_ viewController: UIViewController, animated: Bool = true) {
        navigationController?.pushViewController(viewController, animated: animated)
    }

    func push<V: View>(_ view: V, title: String? = nil, animated: Bool = true) {
        let hostingVC = UIHostingController(rootView: view)
        hostingVC.title = title
        navigationController?.pushViewController(hostingVC, animated: animated)
    }
}

// Inject via environment
private struct NavigationBridgeKey: EnvironmentKey {
    static let defaultValue = NavigationBridge()
}

extension EnvironmentValues {
    var navigationBridge: NavigationBridge {
        get { self[NavigationBridgeKey.self] }
        set { self[NavigationBridgeKey.self] = newValue }
    }
}
```

### Gotchas

- **Back button.** When pushing `UIHostingController` onto a `UINavigationController`, the back button works automatically. Do not add a manual back button in the SwiftUI view.
- **Double navigation bars.** If the SwiftUI view uses `NavigationStack`, it creates its own navigation bar inside the UIKit one. Remove `NavigationStack` from SwiftUI views presented inside `UINavigationController`.
- **Toolbar items.** SwiftUI `.toolbar` items propagate to the UIKit navigation bar when hosted in `UIHostingController`. This works reliably on iOS 16+.

---

## 4. Data Sharing Between UIKit and SwiftUI

### Using `@Observable` (iOS 17+)

The cleanest approach. Create an `@Observable` model, pass it to both UIKit and SwiftUI code:

```swift
@Observable
final class AppState {
    var currentUser: User?
    var unreadCount: Int = 0
    var theme: AppTheme = .system
}

// UIKit side -- read properties directly
let state = AppState()
func viewDidLoad() {
    titleLabel.text = state.currentUser?.name
}

// SwiftUI side -- observation is automatic
struct HeaderView: View {
    let state: AppState

    var body: some View {
        HStack {
            Text(state.currentUser?.name ?? "Guest")
            if state.unreadCount > 0 {
                Badge(count: state.unreadCount)
            }
        }
    }
}
```

### Automatic Observation Tracking in UIKit

For iOS 26+, use UIKit's automatic observation tracking hooks. UIKit tracks `@Observable` properties read inside supported update methods and reruns those methods when the properties change. On iOS 18, add `UIObservationTrackingEnabled` to Info.plist and set it to `YES`; on iOS 26 and later, this key is not required.

```swift
import Observation

@Observable
@MainActor
final class AppState {
    var unreadCount: Int = 0
}

final class DashboardViewController: UIViewController {
    let state: AppState

    private let badgeLabel = UILabel()

    init(state: AppState) {
        self.state = state
        super.init(nibName: nil, bundle: nil)
    }

    required init?(coder: NSCoder) { fatalError("Use init(state:)") }

    override func updateProperties() {
        super.updateProperties()
        badgeLabel.text = "\(state.unreadCount)"
        badgeLabel.isHidden = state.unreadCount == 0
    }
}
```

Use `updateProperties()` for labels, colors, visibility, and other non-layout properties. Use `layoutSubviews()` for geometry work, and use `configurationUpdateHandler` for table or collection view cells.

For iOS 17 back-deployment with `@Observable`, do not describe this as UIKit automatic observation tracking. `@Observable` is available, but UIKit's automatic tracking hooks are not. Manual `withObservationTracking` registrations are one-shot; if you use them, re-register from an explicit invalidation point and avoid polling loops. For iOS 15-16 or existing `ObservableObject` models, subscribe to `objectWillChange`:

```swift
import Combine

final class SettingsViewController: UIViewController {
    let settings: SettingsModel  // ObservableObject
    private var cancellable: AnyCancellable?

    override func viewDidLoad() {
        super.viewDidLoad()
        cancellable = settings.objectWillChange
            .receive(on: RunLoop.main)
            .sink { [weak self] _ in
                self?.updateUI()
            }
    }
}
```

### Gotchas

- **Automatic tracking is scoped.** UIKit only tracks observable properties read inside supported update hooks such as `updateProperties()`, `layoutSubviews()`, or cell configuration update handlers. Arbitrary methods are not tracked automatically.
- **Do not blur iOS 17 with UIKit automatic tracking.** iOS 17 can use Observation manually, but UIKit automatic observation tracking is an iOS 18+ UIKit feature with the iOS 18 `UIObservationTrackingEnabled` key and no key requirement on iOS 26+.
- **Thread safety.** Mutate `@Observable` properties on `@MainActor` when they drive UI in both UIKit and SwiftUI.
- **Retain cycles.** Use `[weak self]` in Combine sinks and task closures. Store cancellables and tasks, then cancel in `deinit`.

---
