# Screen Migration and Hosting Containment

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 1. Screen-by-Screen Migration

Replacing one `UIViewController` at a time with a `UIHostingController` is a common low-risk migration boundary when the screen can remain an isolated unit.

### Strategy

1. Pick a leaf screen (one that does not contain child view controllers).
2. Rewrite its UI in SwiftUI.
3. Replace the UIKit view controller with `UIHostingController` wherever it was instantiated.
4. Wire navigation from the parent UIKit code into the hosting controller.

### Implementation

```swift
// BEFORE: UIKit screen pushed onto a navigation stack
let detailVC = ItemDetailViewController(item: item)
navigationController?.pushViewController(detailVC, animated: true)

// AFTER: SwiftUI screen wrapped in UIHostingController
let detailView = ItemDetailView(item: item)
let hostingVC = UIHostingController(rootView: detailView)
navigationController?.pushViewController(hostingVC, animated: true)
```

### Passing Dismiss/Navigation Callbacks

When the SwiftUI screen needs to pop itself or trigger navigation in the UIKit stack:

```swift
struct ItemDetailView: View {
    let item: Item
    var onDelete: () -> Void

    var body: some View {
        VStack {
            Text(item.title)
            Button("Delete", role: .destructive) {
                onDelete()
            }
        }
    }
}

// In UIKit:
let detailView = ItemDetailView(item: item) {
    self.dataSource.delete(item)
    self.navigationController?.popViewController(animated: true)
}
let hostingVC = UIHostingController(rootView: detailView)
```

### Gotchas

- **Navigation bar.** `UIHostingController` inherits navigation bar visibility from its parent `UINavigationController`. Use `.navigationTitle()` and `.toolbar()` in the SwiftUI view -- they propagate to the UIKit navigation bar automatically.
- **Large titles.** Set `hostingVC.navigationItem.largeTitleDisplayMode` in UIKit code if the SwiftUI `.navigationBarTitleDisplayMode()` modifier does not apply correctly.
- **Tab bar insets.** `UIHostingController` respects `additionalSafeAreaInsets`. If the content overlaps the tab bar, verify safe area propagation.
- **Dismissal.** A `UIHostingController` pushed by UIKit is not in a SwiftUI `NavigationStack`. Pass explicit callbacks for `popViewController`, dismissal, or parent navigation instead of relying on `@Environment(\.dismiss)`.

---

## 2. UIHostingController as Child

Embed SwiftUI sections within an existing UIKit screen. Use when migrating part of a screen (a header, a card, a section) before rewriting the entire controller.

### Implementation

```swift
final class DashboardViewController: UIViewController {
    private var statsHostingController: UIHostingController<StatsCardView>?

    override func viewDidLoad() {
        super.viewDidLoad()

        let statsView = StatsCardView(stats: currentStats)
        let hostingVC = UIHostingController(rootView: statsView)

        // Enable intrinsic sizing so Auto Layout can size the hosted view
        if #available(iOS 16.0, *) {
            hostingVC.sizingOptions = [.intrinsicContentSize]
        }

        addChild(hostingVC)
        hostingVC.view.translatesAutoresizingMaskIntoConstraints = false
        containerView.addSubview(hostingVC.view)

        NSLayoutConstraint.activate([
            hostingVC.view.topAnchor.constraint(equalTo: containerView.topAnchor),
            hostingVC.view.leadingAnchor.constraint(equalTo: containerView.leadingAnchor),
            hostingVC.view.trailingAnchor.constraint(equalTo: containerView.trailingAnchor),
            hostingVC.view.bottomAnchor.constraint(equalTo: containerView.bottomAnchor),
        ])

        hostingVC.didMove(toParent: self)
        statsHostingController = hostingVC
    }

    func updateStats(_ stats: Stats) {
        statsHostingController?.rootView = StatsCardView(stats: stats)
    }
}
```

### With `@Observable` Model

Pass an `@Observable` model to avoid reassigning `rootView` manually. SwiftUI tracks changes automatically:

```swift
@Observable
final class DashboardModel {
    var stats: Stats = .empty
    var isLoading = false
}

struct StatsCardView: View {
    let model: DashboardModel

    var body: some View {
        // Automatically re-renders when model.stats changes
        if model.isLoading {
            ProgressView()
        } else {
            StatsGrid(stats: model.stats)
        }
    }
}

// In UIKit:
let model = DashboardModel()
let hostingVC = UIHostingController(rootView: StatsCardView(model: model))

// Later -- just mutate the model, no rootView reassignment needed
model.stats = newStats
```

### Gotchas

- **Background color.** `UIHostingController`'s view has an opaque system background by default. Set `hostingVC.view.backgroundColor = .clear` if embedding over existing content.
- **sizingOptions on iOS 16+.** Without `.intrinsicContentSize`, the hosted view may report zero size in Auto Layout, causing the container to collapse.
- **Memory.** Store the hosting controller in a property. If it is only held as a child, removing it from the parent deallocates it and the SwiftUI view disappears.

---
