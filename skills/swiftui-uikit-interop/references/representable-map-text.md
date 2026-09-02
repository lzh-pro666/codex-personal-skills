# Map and Text Representable Recipes

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 1. MKMapView Wrapper

Display a map with annotations, track region changes, and toggle map type.

```swift
import SwiftUI
import MapKit

struct MapViewRepresentable: UIViewRepresentable {
    @Binding var region: MKCoordinateRegion
    @Binding var mapType: MKMapType
    var annotations: [MKPointAnnotation]
    var onRegionChanged: ((MKCoordinateRegion) -> Void)?

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> MKMapView {
        let mapView = MKMapView()
        mapView.delegate = context.coordinator
        mapView.showsUserLocation = true
        return mapView
    }

    func updateUIView(_ uiView: MKMapView, context: Context) {
        // Update map type
        if uiView.mapType != mapType {
            uiView.mapType = mapType
        }

        // Update region -- guard against tiny differences to avoid feedback loops
        let currentCenter = uiView.region.center
        let threshold = 0.0001
        if abs(currentCenter.latitude - region.center.latitude) > threshold ||
           abs(currentCenter.longitude - region.center.longitude) > threshold {
            uiView.setRegion(region, animated: true)
        }

        // Diff annotations
        let existing = Set(uiView.annotations.compactMap { $0 as? MKPointAnnotation })
        let incoming = Set(annotations)
        let toRemove = existing.subtracting(incoming)
        let toAdd = incoming.subtracting(existing)
        uiView.removeAnnotations(Array(toRemove))
        uiView.addAnnotations(Array(toAdd))
    }

    final class Coordinator: NSObject, MKMapViewDelegate {
        var parent: MapViewRepresentable

        init(_ parent: MapViewRepresentable) { self.parent = parent }

        func mapView(_ mapView: MKMapView, regionDidChangeAnimated animated: Bool) {
            parent.region = mapView.region
            parent.onRegionChanged?(mapView.region)
        }

        func mapView(
            _ mapView: MKMapView,
            viewFor annotation: MKAnnotation
        ) -> MKAnnotationView? {
            guard !(annotation is MKUserLocation) else { return nil }
            let id = "pin"
            let view = mapView.dequeueReusableAnnotationView(withIdentifier: id)
                ?? MKMarkerAnnotationView(annotation: annotation, reuseIdentifier: id)
            view.annotation = annotation
            return view
        }
    }
}
```

### Usage

```swift
struct MapScreen: View {
    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 37.7749, longitude: -122.4194),
        span: MKCoordinateSpan(latitudeDelta: 0.05, longitudeDelta: 0.05)
    )
    @State private var mapType: MKMapType = .standard

    var body: some View {
        MapViewRepresentable(
            region: $region,
            mapType: $mapType,
            annotations: []
        )
        .ignoresSafeArea()
    }
}
```

### Gotchas

- **Region update loops.** The delegate writes to `@Binding region`, which triggers `updateUIView`, which calls `setRegion`, which triggers the delegate again. The threshold guard is essential.
- **Annotation diffing.** MKMapView does not handle duplicate annotations well. Always diff before adding/removing.
- **Native SwiftUI Map.** For iOS 17+, prefer the native `Map` view unless you need delegate-level control (custom overlays, clustering, etc.).

---

## 2. UITextView Wrapper (Attributed Text)

Wrap `UITextView` for rich text editing with `NSAttributedString` binding and placeholder support.

```swift
import SwiftUI

struct RichTextEditor: UIViewRepresentable {
    @Binding var attributedText: NSAttributedString
    var placeholder: String = ""
    @Binding var isFirstResponder: Bool

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIView(context: Context) -> UITextView {
        let textView = UITextView()
        textView.delegate = context.coordinator
        textView.font = .preferredFont(forTextStyle: .body)
        textView.adjustsFontForContentSizeCategory = true
        textView.backgroundColor = .clear
        textView.textContainerInset = UIEdgeInsets(top: 8, left: 4, bottom: 8, right: 4)

        // Placeholder label
        let label = UILabel()
        label.text = placeholder
        label.font = .preferredFont(forTextStyle: .body)
        label.textColor = .placeholderText
        label.tag = 999
        label.translatesAutoresizingMaskIntoConstraints = false
        textView.addSubview(label)
        NSLayoutConstraint.activate([
            label.topAnchor.constraint(equalTo: textView.topAnchor, constant: 8),
            label.leadingAnchor.constraint(equalTo: textView.leadingAnchor, constant: 8),
        ])

        return textView
    }

    func updateUIView(_ uiView: UITextView, context: Context) {
        if uiView.attributedText != attributedText {
            uiView.attributedText = attributedText
        }

        // Update placeholder visibility
        if let label = uiView.viewWithTag(999) as? UILabel {
            label.isHidden = !uiView.text.isEmpty
        }

        // First responder management
        if isFirstResponder && !uiView.isFirstResponder {
            uiView.becomeFirstResponder()
        } else if !isFirstResponder && uiView.isFirstResponder {
            uiView.resignFirstResponder()
        }
    }

    @available(iOS 16.0, *)
    func sizeThatFits(
        _ proposal: ProposedViewSize,
        uiView: UITextView,
        context: Context
    ) -> CGSize? {
        let width = proposal.width ?? UIView.layoutFittingExpandedSize.width
        let size = uiView.sizeThatFits(CGSize(width: width, height: .greatestFiniteMagnitude))
        return CGSize(width: width, height: max(size.height, 44))
    }

    final class Coordinator: NSObject, UITextViewDelegate {
        var parent: RichTextEditor

        init(_ parent: RichTextEditor) { self.parent = parent }

        func textViewDidChange(_ textView: UITextView) {
            parent.attributedText = textView.attributedText ?? NSAttributedString()
            if let label = textView.viewWithTag(999) as? UILabel {
                label.isHidden = !textView.text.isEmpty
            }
        }

        func textViewDidBeginEditing(_ textView: UITextView) {
            parent.isFirstResponder = true
        }

        func textViewDidEndEditing(_ textView: UITextView) {
            parent.isFirstResponder = false
        }
    }
}
```

### Usage

```swift
struct NotesEditorView: View {
    @State private var text = NSAttributedString()
    @State private var isFocused = false

    var body: some View {
        RichTextEditor(
            attributedText: $text,
            placeholder: "Write something...",
            isFirstResponder: $isFocused
        )
        .frame(minHeight: 100)
    }
}
```

### Gotchas

- **`NSAttributedString` comparison.** The equality check in `updateUIView` is critical -- without it, every keystroke triggers a full re-render loop.
- **First responder management.** Avoid calling `becomeFirstResponder()` unconditionally in `updateUIView` -- it steals focus from other fields.
- **iOS 26 alternative.** `TextEditor` in iOS 26 supports `AttributedString` natively. Prefer it unless you need `NSAttributedString` or delegate-level control.

---
