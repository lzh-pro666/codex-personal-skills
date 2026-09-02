# System Presenter Representable Recipes

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## 5. MFMailComposeViewController Wrapper

Present the system email composer with pre-filled fields and handle the result.

```swift
import SwiftUI
import MessageUI

struct MailComposer: UIViewControllerRepresentable {
    let subject: String
    let recipients: [String]
    let body: String
    var isHTML: Bool = false
    var onResult: ((MFMailComposeResult) -> Void)?
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> MFMailComposeViewController {
        let controller = MFMailComposeViewController()
        controller.mailComposeDelegate = context.coordinator
        controller.setSubject(subject)
        controller.setToRecipients(recipients)
        controller.setMessageBody(body, isHTML: isHTML)
        return controller
    }

    func updateUIViewController(_ uiViewController: MFMailComposeViewController, context: Context) {
        // Cannot update mail compose after presentation
    }

    final class Coordinator: NSObject, MFMailComposeViewControllerDelegate {
        let parent: MailComposer

        init(_ parent: MailComposer) { self.parent = parent }

        func mailComposeController(
            _ controller: MFMailComposeViewController,
            didFinishWith result: MFMailComposeResult,
            error: Error?
        ) {
            parent.onResult?(result)
            parent.dismiss()
        }
    }
}
```

### Usage

```swift
struct FeedbackView: View {
    @State private var showMail = false

    var body: some View {
        Button("Send Feedback") {
            guard MFMailComposeViewController.canSendMail() else { return }
            showMail = true
        }
        .sheet(isPresented: $showMail) {
            MailComposer(
                subject: "App Feedback",
                recipients: ["support@example.com"],
                body: "I have feedback about..."
            ) { result in
                print("Mail result: \(result.rawValue)")
            }
        }
    }
}
```

### Gotchas

- **Check `canSendMail()` before presenting.** If it returns `false`, do not display `MFMailComposeViewController`; show fallback UI or disable the mail action.
- **Cannot update after presentation.** `updateUIViewController` is intentionally empty -- the mail compose API does not support changing fields after the controller is shown.
- **The delegate protocol name is `MFMailComposeViewControllerDelegate`**, not `MFMailComposeDelegate`.

---

## 6. UIActivityViewController Wrapper (Share Sheet)

Present the system share sheet. This is a `UIViewControllerRepresentable` because `UIActivityViewController` is a controller, not a view.

```swift
import SwiftUI

struct ShareSheet: UIViewControllerRepresentable {
    let items: [Any]
    var activities: [UIActivity]? = nil
    var excludedTypes: [UIActivity.ActivityType]? = nil

    func makeUIViewController(context: Context) -> UIActivityViewController {
        let controller = UIActivityViewController(
            activityItems: items,
            applicationActivities: activities
        )
        controller.excludedActivityTypes = excludedTypes
        return controller
    }

    func updateUIViewController(_ uiViewController: UIActivityViewController, context: Context) {
        // Cannot update after presentation
    }
}
```

### Usage

```swift
struct ContentView: View {
    @State private var showShare = false

    var body: some View {
        Button("Share") { showShare = true }
            .sheet(isPresented: $showShare) {
                ShareSheet(items: ["Check out this app!", URL(string: "https://example.com")!])
                    .presentationDetents([.medium])
            }
    }
}
```

### Gotchas

- **Present via `.sheet`.** Do not try to use `UIActivityViewController` as an inline view -- it is a modal controller.
- **iPad requires `popoverPresentationController`.** When using on iPad outside of `.sheet`, set the source view/rect on the popover controller. SwiftUI's `.sheet` handles this automatically.
- **iOS 16+ alternative.** `ShareLink` is a native SwiftUI view for Transferable items. Prefer it for simple sharing.

---

## 9. MFMessageComposeViewController Wrapper

Present the system SMS/MMS composer with pre-filled recipients, body, and optional attachments. Companion to Recipe 6 (MFMailComposeViewController).

```swift
import SwiftUI
import MessageUI

struct MessageComposer: UIViewControllerRepresentable {
    let recipients: [String]
    let body: String
    var attachments: [MessageAttachment] = []
    var onResult: ((MessageComposeResult) -> Void)?
    @Environment(\.dismiss) private var dismiss

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    func makeUIViewController(context: Context) -> MFMessageComposeViewController {
        let controller = MFMessageComposeViewController()
        controller.messageComposeDelegate = context.coordinator
        controller.recipients = recipients
        controller.body = body

        for attachment in attachments {
            controller.addAttachmentData(
                attachment.data,
                typeIdentifier: attachment.typeIdentifier,
                filename: attachment.filename
            )
        }

        return controller
    }

    func updateUIViewController(
        _ uiViewController: MFMessageComposeViewController,
        context: Context
    ) {
        // Cannot update message compose after presentation
    }

    final class Coordinator: NSObject, MFMessageComposeViewControllerDelegate {
        let parent: MessageComposer

        init(_ parent: MessageComposer) { self.parent = parent }

        func messageComposeViewController(
            _ controller: MFMessageComposeViewController,
            didFinishWith result: MessageComposeResult
        ) {
            parent.onResult?(result)
            parent.dismiss()
        }
    }
}

struct MessageAttachment {
    let data: Data
    let typeIdentifier: String // UTI, e.g., "public.jpeg"
    let filename: String
}
```

### Usage

```swift
struct InviteView: View {
    @State private var showMessage = false

    var body: some View {
        Button("Send Invite via SMS") {
            guard MFMessageComposeViewController.canSendText() else { return }
            showMessage = true
        }
        .sheet(isPresented: $showMessage) {
            MessageComposer(
                recipients: ["+1234567890"],
                body: "Join me on this app!"
            ) { result in
                switch result {
                case .sent:
                    print("Message sent")
                case .cancelled:
                    print("User cancelled")
                case .failed:
                    print("Message failed")
                @unknown default:
                    break
                }
            }
        }
    }
}
```

### With Image Attachment

```swift
struct SharePhotoView: View {
    @State private var showMessage = false
    let image: UIImage

    var body: some View {
        Button("Send Photo") {
            guard MFMessageComposeViewController.canSendText(),
                  MFMessageComposeViewController.canSendAttachments() else {
                return
            }
            showMessage = true
        }
        .sheet(isPresented: $showMessage) {
            MessageComposer(
                recipients: [],
                body: "Check out this photo!",
                attachments: [
                    MessageAttachment(
                        data: image.jpegData(compressionQuality: 0.8) ?? Data(),
                        typeIdentifier: "public.jpeg",
                        filename: "photo.jpg"
                    )
                ]
            )
        }
    }
}
```

### Gotchas

- **Check `canSendText()` before presenting.** If it returns `false`, do not display `MFMessageComposeViewController`; show fallback UI or disable the message action.
- **Check `canSendAttachments()` before adding attachments.** Not all devices or carriers support MMS attachments.
- **The delegate protocol is `MFMessageComposeViewControllerDelegate`**, not `MFMessageComposeDelegate`. It has a single required method.
- **Cannot update after presentation.** Like `MFMailComposeViewController`, the message composer API does not support changing fields after the controller is shown.
- **iMessage vs. SMS.** The controller automatically uses iMessage when available. You cannot force one protocol over the other.
- **Simulator limitation.** `canSendText()` returns `false` on the simulator. Test on a physical device.

> **Docs:** [MFMessageComposeViewController](https://developer.apple.com/documentation/messageui/mfmessagecomposeviewcontroller) | [MFMessageComposeViewControllerDelegate](https://developer.apple.com/documentation/messageui/mfmessagecomposeviewcontrollerdelegate)
