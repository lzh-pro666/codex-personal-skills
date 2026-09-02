# Media and Picker Representable Recipes

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 3. AVCaptureVideoPreviewLayer Wrapper

Display a live camera preview. The preview layer requires a `UIView` host.

```swift
import SwiftUI
import AVFoundation

struct CameraPreview: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> CameraPreviewUIView {
        let view = CameraPreviewUIView()
        view.previewLayer.session = session
        view.previewLayer.videoGravity = .resizeAspectFill
        return view
    }

    func updateUIView(_ uiView: CameraPreviewUIView, context: Context) {
        // Session is reference type -- no update needed unless swapping sessions
        if uiView.previewLayer.session !== session {
            uiView.previewLayer.session = session
        }
    }
}

final class CameraPreviewUIView: UIView {
    override class var layerClass: AnyClass { AVCaptureVideoPreviewLayer.self }

    var previewLayer: AVCaptureVideoPreviewLayer {
        layer as! AVCaptureVideoPreviewLayer
    }

    override func layoutSubviews() {
        super.layoutSubviews()
        previewLayer.frame = bounds
    }
}
```

### Usage

```swift
struct CameraScreen: View {
    @State private var cameraManager = CameraManager()

    var body: some View {
        CameraPreview(session: cameraManager.session)
            .ignoresSafeArea()
            .task { await cameraManager.start() }
    }
}
```

### Gotchas

- **Use a custom UIView subclass with `layerClass`.** Overriding `layerClass` avoids adding a sublayer and ensures the preview layer resizes automatically with the view.
- **Session management belongs outside the representable.** Create and manage `AVCaptureSession` in a separate model. The representable only displays it.
- **Orientation.** Set `previewLayer.connection?.videoRotationAngle` if supporting device rotation.

---

## 4. PHPickerViewController Wrapper

Multi-select photo picker that loads selected images asynchronously.

```swift
import SwiftUI
import PhotosUI

struct PhotoPicker: UIViewControllerRepresentable {
    @Binding var selectedImages: [UIImage]
    var selectionLimit: Int = 0  // 0 = unlimited
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> PHPickerViewController {
        var config = PHPickerConfiguration(photoLibrary: .shared())
        config.filter = .images
        config.selectionLimit = selectionLimit
        config.preferredAssetRepresentationMode = .current

        let picker = PHPickerViewController(configuration: config)
        picker.delegate = context.coordinator
        return picker
    }

    func updateUIViewController(_ uiViewController: PHPickerViewController, context: Context) {
        // Nothing to update -- configuration is immutable after creation
    }

    final class Coordinator: NSObject, PHPickerViewControllerDelegate {
        let parent: PhotoPicker

        init(_ parent: PhotoPicker) { self.parent = parent }

        func picker(
            _ picker: PHPickerViewController,
            didFinishPicking results: [PHPickerResult]
        ) {
            parent.dismiss()

            guard !results.isEmpty else { return }

            Task { @MainActor in
                var images: [UIImage] = []
                for result in results {
                    if let image = await loadImage(from: result.itemProvider) {
                        images.append(image)
                    }
                }
                parent.selectedImages = images
            }
        }

        private func loadImage(from provider: NSItemProvider) async -> UIImage? {
            await withCheckedContinuation { continuation in
                if provider.canLoadObject(ofClass: UIImage.self) {
                    provider.loadObject(ofClass: UIImage.self) { image, _ in
                        continuation.resume(returning: image as? UIImage)
                    }
                } else {
                    continuation.resume(returning: nil)
                }
            }
        }
    }
}
```

### Usage

```swift
struct ImagePickerDemo: View {
    @State private var images: [UIImage] = []
    @State private var showPicker = false

    var body: some View {
        VStack {
            ScrollView(.horizontal) {
                HStack {
                    ForEach(images.indices, id: \.self) { i in
                        Image(uiImage: images[i])
                            .resizable()
                            .scaledToFill()
                            .frame(width: 100, height: 100)
                            .clipShape(.rect(cornerRadius: 8))
                    }
                }
            }
            Button("Pick Photos") { showPicker = true }
        }
        .sheet(isPresented: $showPicker) {
            PhotoPicker(selectedImages: $images, selectionLimit: 5)
        }
    }
}
```

### Gotchas

- **Always dismiss in the delegate.** `picker(_:didFinishPicking:)` is called for both selection and cancellation (with empty results). Dismiss in both cases.
- **Async image loading.** `NSItemProvider.loadObject` is completion-based. Wrap in `withCheckedContinuation` for async/await usage. Load images after dismissal to avoid blocking the picker UI.
- **iOS 17 alternative.** `PhotosUI.PhotosPicker` is a native SwiftUI view. Prefer it unless you need custom picker UI or advanced filtering.

---
