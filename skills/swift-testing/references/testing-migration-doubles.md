# XCTest Migration and Test Doubles

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## XCTest Migration Patterns

Swift Testing tests are functions annotated with `@Test`; they do not need `XCTestCase`. Use the smallest shape that needs the fixture:

```swift
@Test func validatesTotal() {
    #expect(Cart(items: [.sample]).total == 9.99)
}

@Suite("Checkout")
struct CheckoutTests {
    let calculator = PriceCalculator()

    @Test func appliesDiscount() {
        #expect(calculator.total(discount: .percent(10)) == 8.99)
    }
}

@Suite("Shared Cache")
actor CacheTests {
    var cache = TestCache()

    @Test func storesValue() async {
        await cache.store("value", forKey: "key")
        #expect(await cache.value(forKey: "key") == "value")
    }
}

struct PureHelperTests {
    @Test static func normalizesInput() {
        #expect(normalize("  email@example.com ") == "email@example.com")
    }
}
```

Common XCTest mappings:

| XCTest | Swift Testing |
|---|---|
| `XCTAssertTrue(x)` / `XCTAssert(x)` | `#expect(x)` |
| `XCTAssertFalse(x)` | `#expect(!x)` |
| `XCTAssertEqual(a, b)` | `#expect(a == b)` |
| `XCTAssertThrowsError(try f())` | `#expect(throws: (any Error).self) { try f() }` |
| `XCTAssertNoThrow(try f())` | `#expect(throws: Never.self) { try f() }` |
| `try XCTUnwrap(value)` | `try #require(value)` |
| `XCTFail("message")` | `Issue.record("message")` |

Convert `setUp` into isolated suite `init()` state. Avoid moving fixtures into singletons or shared globals; Swift Testing runs tests in parallel by default. Use actors or per-test fixtures for mutable test doubles, and use `.serialized` only when an external shared resource cannot be isolated.

### XCTest Interoperability During Migration

XCTest and Swift Testing can coexist in the same target, bundle, and even source file during migration. Xcode 27 is the important dividing line for migration reviews: test plans created before Xcode 27 inherit the older `limited` behavior, while new Xcode 27 projects use `complete` behavior by default. Test framework interoperability controls how issues cross that boundary:

- `limited`: preserves the older migration behavior. Cross-framework issues from XCTest are warnings, so a Swift Testing test that reuses a helper wrapping `XCTFail` may still pass while showing migration warnings. Test plans created before Xcode 27 inherit this mode.
- `complete`: treats XCTest assertions and Swift Testing issues as test issues across both frameworks. New Xcode 27 projects use this mode by default, and it is the preferred migration default when available.
- `strict`: like `complete`, but cross-framework issues from XCTest are fatal so teams catch stale helper usage quickly.
- `none`: disables interop and should be reserved for projects that intentionally forbid mixed helpers.

For SwiftPM, set `SWIFT_TESTING_XCTEST_INTEROP_MODE` when the package needs an explicit mode. A package still declaring `swift-tools-version: 6.3` can run under the Swift 6.4 toolchain with limited-mode behavior; updating the package to Swift tools version 6.4 or newer moves the default to complete-mode behavior.

Do not tell teams that all cross-framework APIs are categorically disallowed. Instead, keep existing helper code working under `complete` or `strict` while migrating toward native Swift Testing issue-reporting:

```swift
// Transitional helper body
func requireUser(_ user: User?) throws -> User {
    try #require(user, "Expected a user")
}

func recordMissingUser() {
    Issue.record("Expected a user")
}
```

Use native Swift Testing APIs for new Swift Testing tests. Keep UI automation, performance measurement, and Objective-C exception tests in XCTest.

## Mocking and Test Doubles

Define testable boundaries with protocols:

```swift
protocol UserRepository: Sendable {
    func fetch(id: String) async throws -> User
    func save(_ user: User) async throws
}

actor MockUserRepository: UserRepository {
    var users: [String: User] = [:]
    var fetchError: (any Error)?
    private(set) var savedUsers: [User] = []

    init(users: [String: User] = [:], fetchError: (any Error)? = nil) {
        self.users = users
        self.fetchError = fetchError
    }

    func fetch(id: String) async throws -> User {
        if let error = fetchError { throw error }
        guard let user = users[id] else { throw NotFoundError() }
        return user
    }

    func save(_ user: User) async throws {
        savedUsers.append(user)
        users[user.id] = user
    }
}
```

**Pattern:** Mocks conform to protocols, never subclass concrete types. For parallel Swift Testing runs, keep mutable mock state isolated in an actor or another Sendable-safe fixture. Store call counts and arguments for verification behind that isolation boundary.

## Testable Architecture

Inject dependencies through initializers for testability:

```swift
@Observable
class ProfileViewModel {
    var user: User?
    var error: Error?
    private let repository: any UserRepository

    init(repository: any UserRepository) {
        self.repository = repository
    }

    func load() async {
        do {
            user = try await repository.fetch(id: "current")
        } catch {
            self.error = error
        }
    }
}

// Test with mock
@Test @MainActor func viewModelLoadsUser() async {
    let mock = MockUserRepository(users: ["current": .preview])
    let vm = ProfileViewModel(repository: mock)
    await vm.load()
    #expect(vm.user?.name == "Alice")
}

@Test @MainActor func viewModelHandlesError() async {
    let mock = MockUserRepository(fetchError: URLError(.notConnectedToInternet))
    let vm = ProfileViewModel(repository: mock)
    await vm.load()
    #expect(vm.user == nil)
    #expect(vm.error != nil)
}
```
