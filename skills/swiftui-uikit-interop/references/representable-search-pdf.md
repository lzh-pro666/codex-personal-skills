# Search and PDF Representable Recipes

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 7. UISearchBar Wrapper

Wrap `UISearchBar` with delegate-based callbacks, debounce support, and cancel button handling.

```swift
import SwiftUI
import Combine

struct SearchBar: UIViewRepresentable {
    @Binding var text: String
    var placeholder: String = "Search"
    var onSearch: ((String) -> Void)?
    var onCancel: (() -> Void)?

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> UISearchBar {
        let searchBar = UISearchBar()
        searchBar.delegate = context.coordinator
        searchBar.placeholder = placeholder
        searchBar.searchBarStyle = .minimal
        searchBar.autocapitalizationType = .none
        return searchBar
    }

    func updateUIView(_ uiView: UISearchBar, context: Context) {
        if uiView.text != text {
            uiView.text = text
        }
    }

    final class Coordinator: NSObject, UISearchBarDelegate {
        var parent: SearchBar
        private var debounceTask: Task<Void, Never>?

        init(_ parent: SearchBar) { self.parent = parent }

        func searchBar(_ searchBar: UISearchBar, textDidChange searchText: String) {
            parent.text = searchText
            searchBar.showsCancelButton = !searchText.isEmpty

            // Debounce search
            debounceTask?.cancel()
            debounceTask = Task { @MainActor in
                try? await Task.sleep(for: .milliseconds(300))
                guard !Task.isCancelled else { return }
                parent.onSearch?(searchText)
            }
        }

        func searchBarSearchButtonClicked(_ searchBar: UISearchBar) {
            debounceTask?.cancel()
            parent.onSearch?(parent.text)
            searchBar.resignFirstResponder()
        }

        func searchBarCancelButtonClicked(_ searchBar: UISearchBar) {
            parent.text = ""
            parent.onCancel?()
            searchBar.resignFirstResponder()
            searchBar.showsCancelButton = false
        }
    }
}
```

### Usage

```swift
struct SearchableList: View {
    @State private var query = ""
    @State private var results: [String] = []

    var body: some View {
        VStack(spacing: 0) {
            SearchBar(text: $query, placeholder: "Search items") { text in
                results = performSearch(text)
            }
            List(results, id: \.self) { Text($0) }
        }
    }
}
```

### Gotchas

- **Native `.searchable` modifier.** Prefer SwiftUI's `.searchable(text:)` modifier for standard search patterns. Use this wrapper only when you need precise control over search bar appearance or delegate timing.
- **Debounce with `Task.sleep`.** Cancel the previous task before starting a new one to debounce. `Combine` is not needed.
- **Cancel button state.** Toggle `showsCancelButton` in the delegate, not in `updateUIView`, to avoid layout jumps.

---

## 8. PDFView Wrapper (PDFKit)

Display PDF documents in SwiftUI using `PDFView` from PDFKit. Supports loading from URL, Data, or file path, with configurable display mode and auto-scaling.

```swift
import SwiftUI
import PDFKit

struct PDFViewer: UIViewRepresentable {
    let document: PDFDocument?
    var displayMode: PDFDisplayMode = .singlePageContinuous
    var autoScales: Bool = true
    var displayDirection: PDFDisplayDirection = .vertical
    var pageShadowsEnabled: Bool = true

    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.displayMode = displayMode
        pdfView.displayDirection = displayDirection
        pdfView.autoScales = autoScales
        pdfView.pageShadowsEnabled = pageShadowsEnabled
        pdfView.document = document
        return pdfView
    }

    func updateUIView(_ uiView: PDFView, context: Context) {
        // Update document if it changed (reference comparison)
        if uiView.document !== document {
            uiView.document = document
        }

        if uiView.displayMode != displayMode {
            uiView.displayMode = displayMode
        }

        if uiView.autoScales != autoScales {
            uiView.autoScales = autoScales
        }
    }
}
```

### Convenience Initializers

```swift
extension PDFViewer {
    /// Load a PDF from a URL (local file or remote).
    init(url: URL, displayMode: PDFDisplayMode = .singlePageContinuous) {
        self.document = PDFDocument(url: url)
        self.displayMode = displayMode
    }

    /// Load a PDF from raw data.
    init(data: Data, displayMode: PDFDisplayMode = .singlePageContinuous) {
        self.document = PDFDocument(data: data)
        self.displayMode = displayMode
    }
}
```

### Usage

```swift
struct DocumentView: View {
    let pdfURL: URL

    var body: some View {
        PDFViewer(url: pdfURL)
            .ignoresSafeArea(edges: .bottom)
            .navigationTitle("Document")
            .navigationBarTitleDisplayMode(.inline)
    }
}
```

### With Async Loading

```swift
struct RemotePDFView: View {
    let url: URL
    @State private var document: PDFDocument?
    @State private var isLoading = true
    @State private var errorMessage: String?

    var body: some View {
        Group {
            if let document {
                PDFViewer(document: document)
            } else if isLoading {
                ProgressView("Loading PDF...")
            } else if let errorMessage {
                ContentUnavailableView(
                    "Could Not Load PDF",
                    systemImage: "doc.text.fill",
                    description: Text(errorMessage)
                )
            }
        }
        .task {
            do {
                let (data, _) = try await URLSession.shared.data(from: url)
                document = PDFDocument(data: data)
            } catch {
                errorMessage = error.localizedDescription
            }
            isLoading = false
        }
    }
}
```

### PDFView with Page Navigation

```swift
struct NavigablePDFView: UIViewRepresentable {
    let document: PDFDocument?
    @Binding var currentPageIndex: Int

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> PDFView {
        let pdfView = PDFView()
        pdfView.displayMode = .singlePageContinuous
        pdfView.autoScales = true
        pdfView.document = document

        NotificationCenter.default.addObserver(
            context.coordinator,
            selector: #selector(Coordinator.pageChanged(_:)),
            name: .PDFViewPageChanged,
            object: pdfView
        )

        return pdfView
    }

    func updateUIView(_ uiView: PDFView, context: Context) {
        if uiView.document !== document {
            uiView.document = document
        }

        // Navigate to page if binding changed externally
        if let doc = uiView.document,
           let page = doc.page(at: currentPageIndex),
           uiView.currentPage != page {
            uiView.go(to: page)
        }
    }

    static func dismantleUIView(_ uiView: PDFView, coordinator: Coordinator) {
        NotificationCenter.default.removeObserver(coordinator)
    }

    final class Coordinator: NSObject {
        var parent: NavigablePDFView

        init(_ parent: NavigablePDFView) { self.parent = parent }

        @objc func pageChanged(_ notification: Notification) {
            guard let pdfView = notification.object as? PDFView,
                  let currentPage = pdfView.currentPage,
                  let document = pdfView.document else { return }
            let index = document.index(for: currentPage)
            if parent.currentPageIndex != index {
                parent.currentPageIndex = index
            }
        }
    }
}
```

### Gotchas

- **`PDFView` inherits from `UIView`.** Use `UIViewRepresentable`, not `UIViewControllerRepresentable`.
- **Document is a reference type.** Use `!==` for identity comparison in `updateUIView` to avoid unnecessary reloads.
- **Page change notifications.** Use `NotificationCenter` with `.PDFViewPageChanged` -- `PDFView` does not use a delegate pattern for page changes.
- **Remove observers in `dismantleUIView`.** Failing to remove `NotificationCenter` observers causes crashes after the view is removed.
- **`autoScales`** fits the PDF to the view width. Disable it if you want the user to start at a specific zoom level.
- **Thread safety.** `PDFDocument` loading can be expensive. Load asynchronously and assign on the main thread.

> **Docs:** [PDFView](https://developer.apple.com/documentation/pdfkit/pdfview) | [PDFKit](https://developer.apple.com/documentation/pdfkit)

---
