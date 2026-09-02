# Async, UI, Performance, and Snapshot Testing

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Async and Concurrent Tests

```swift
@Test @MainActor func viewModelUpdatesOnMainActor() async {
    let vm = ProfileViewModel(repository: MockUserRepository())
    await vm.load()
    #expect(vm.user != nil)
}

// Clock injection for time-dependent logic
@Test func debounceUsesCorrectDelay() async throws {
    let clock = TestClock()
    let debouncer = Debouncer(delay: .seconds(1), clock: clock)
    debouncer.submit { /* action */ }
    await clock.advance(by: .milliseconds(500))
    #expect(!debouncer.hasExecuted)
    await clock.advance(by: .milliseconds(500))
    #expect(debouncer.hasExecuted)
}

// Error path testing
@Test func fetchThrowsOnNetworkError() async {
    let mock = MockUserRepository(fetchError: URLError(.notConnectedToInternet))
    #expect(throws: URLError.self) {
        try await mock.fetch(id: "1")
    }
}
```

## XCTest UI Tests — Page Object Pattern

Swift Testing does not support UI testing. Use XCTest with XCUITest for all UI tests.

```swift
class LoginUITests: XCTestCase {
    let app = XCUIApplication()

    override func setUpWithError() throws {
        continueAfterFailure = false
        app.launch()
    }

    func testLoginFlow() throws {
        let loginPage = LoginPage(app: app)
        let homePage = loginPage.login(email: "test@test.com", password: "password")
        XCTAssertTrue(homePage.welcomeLabel.exists)
    }
}
```

### Page Object Pattern

Encapsulate UI element queries in page objects for reusable, readable UI tests:

```swift
struct LoginPage {
    let app: XCUIApplication
    var emailField: XCUIElement { app.textFields["Email"] }
    var passwordField: XCUIElement { app.secureTextFields["Password"] }
    var signInButton: XCUIElement { app.buttons["Sign In"] }

    @discardableResult
    func login(email: String, password: String) -> HomePage {
        emailField.tap(); emailField.typeText(email)
        passwordField.tap(); passwordField.typeText(password)
        signInButton.tap()
        return HomePage(app: app)
    }
}

struct HomePage {
    let app: XCUIApplication
    var welcomeLabel: XCUIElement { app.staticTexts["Welcome"] }
}
```

## Performance Testing

```swift
class FeedPerformanceTests: XCTestCase {
    func testFeedParsingPerformance() throws {
        let data = try loadFixture("large-feed.json")
        let metrics: [XCTMetric] = [XCTClockMetric(), XCTMemoryMetric()]
        measure(metrics: metrics) {
            _ = try? FeedParser.parse(data)
        }
    }
}
```

Performance tests require XCTest — not available in Swift Testing.

## Snapshot Testing

When the repository already uses Point-Free's `SnapshotTesting`, use it for focused visual regression. Do not add a snapshot dependency merely to follow this example. Snapshot testing requires XCTest:

```swift
import SnapshotTesting
import XCTest

class ProfileViewSnapshotTests: XCTestCase {
    func testProfileView() {
        let view = ProfileView(user: .preview)
        assertSnapshot(of: view, as: .image(layout: .device(config: .iPhone13)))

        // Dark mode
        assertSnapshot(of: view.environment(\.colorScheme, .dark),
                       as: .image(layout: .device(config: .iPhone13)), named: "dark")

        // Large Dynamic Type
        assertSnapshot(of: view.environment(\.dynamicTypeSize, .accessibility3),
                       as: .image(layout: .device(config: .iPhone13)), named: "largeText")
    }
}
```

Cover appearance and Dynamic Type variants only when they are relevant to the affected UI contract. Read `testing-advanced.md` for attachments, exit tests, warnings, and cancellation APIs so ordinary test work does not duplicate version-gated guidance.
