# Swift Testing Core Patterns

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Basic Tests and Traits

```swift
import Testing

@Test("User can update their display name")
func updateDisplayName() {
    var user = User(name: "Alice")
    user.name = "Bob"
    #expect(user.name == "Bob")
}

@Test(.tags(.validation, .email))
func validatesEmailFormat() { /* ... */ }
```

## Expectations and Requirements

```swift
#expect(result == 42)
#expect(name.isEmpty == false)
#expect(items.count > 0, "Items should not be empty")

// Error type checking
#expect(throws: ValidationError.self) {
    try validate(email: "not-an-email")
}

// Specific error matching
#expect {
    try validate(email: "")
} throws: { error in
    guard let err = error as? ValidationError else { return false }
    return err == .empty
}

// #require unwraps or fails the test
let user = try #require(await fetchUser(id: 1))
let first = try #require(items.first)
```

**Rule: Use `#require` when subsequent assertions depend on the value. Use `#expect` for independent checks.**

## Suite Organization

```swift
@Suite("User Authentication")
struct AuthTests {
    let service: AuthService
    let mockRepo: MockUserRepository

    // init() replaces setUp() -- runs before each test
    init() {
        mockRepo = MockUserRepository()
        service = AuthService(repository: mockRepo)
    }

    @Test func loginSucceeds() async throws {
        let user = try await service.login(email: "test@test.com", password: "pass")
        #expect(user.email == "test@test.com")
    }

    @Test func loginFailsWithBadPassword() async {
        #expect(throws: AuthError.invalidCredentials) {
            try await service.login(email: "test@test.com", password: "wrong")
        }
    }
}
```

Suites can nest for logical grouping:

```swift
@Suite("Payments")
struct PaymentTests {
    @Suite("Subscriptions")
    struct SubscriptionTests {
        @Test func renewsAutomatically() { /* ... */ }
    }
    @Suite("One-Time")
    struct OneTimeTests {
        @Test func chargesCorrectAmount() { /* ... */ }
    }
}
```

## Parameterized Tests

```swift
@Test("Email validation", arguments: [
    ("user@example.com", true),
    ("user@", false),
    ("@example.com", false),
    ("", false),
])
func validateEmail(email: String, isValid: Bool) {
    #expect(EmailValidator.isValid(email) == isValid)
}

// From CaseIterable
@Test(arguments: Currency.allCases)
func currencyHasSymbol(currency: Currency) {
    #expect(currency.symbol.isEmpty == false)
}

// Two collections: cartesian product
@Test(arguments: [1, 2, 3], ["a", "b"])
func combinations(number: Int, letter: String) {
    #expect(number > 0)
}

// Use zip for 1:1 pairing
@Test(arguments: zip(["USD", "EUR"], ["$", "€"]))
func currencySymbols(code: String, symbol: String) {
    #expect(Currency(code: code).symbol == symbol)
}
```

Each argument combination runs as an independent test case reported separately.

## Execution Model

Swift Testing uses Swift Concurrency and runs tests in parallel by default. Treat every test as isolated work unless you explicitly serialize a scope.

```swift
@Suite(.serialized, .tags(.database))
struct DatabaseTests {
    @Test func insertsRecord() async throws { /* ... */ }
    @Test func removesRecord() async throws { /* ... */ }
}
```

Use `.serialized` when tests must not overlap because they touch shared external state like a keychain, database, singleton service, or filesystem location. It does not make unrelated tests outside the serialized scope run one-at-a-time.

Important implications:
- Each test gets its own suite instance.
- Declaration order is not a contract.
- If one logical workflow depends on previous state, keep that workflow inside one test.
- Prefer isolated fixtures over shared mutable globals.

## Confirmation and Known Issues

### Confirmation (Async Event Testing)

```swift
// Basic confirmation -- event must fire exactly once
await confirmation("Received notification") { confirm in
    let observer = NotificationCenter.default.addObserver(
        forName: .userLoggedIn, object: nil, queue: .main
    ) { _ in confirm() }
    await authService.login()
    NotificationCenter.default.removeObserver(observer)
}

// Expected count -- event must fire exactly N times
await confirmation("Received 3 items", expectedCount: 3) { confirm in
    processor.onItem = { _ in confirm() }
    await processor.process(items)
}
```

### Known Issues

```swift
// Known failing test -- does not count as failure
withKnownIssue("Propane tank is empty") {
    #expect(truck.grill.isHeating)
}

// Intermittent / flaky
withKnownIssue(isIntermittent: true) {
    #expect(service.isReachable)
}

// Conditional
withKnownIssue {
    #expect(foodTruck.grill.isHeating)
} when: {
    !hasPropane
}

// Match specific issues only
try withKnownIssue {
    let level = try #require(foodTruck.batteryLevel)
    #expect(level >= 0.8)
} matching: { issue in
    guard case .expectationFailed(let expectation) = issue.kind else { return false }
    return expectation.isRequired
}
```

If no known issues are recorded, Swift Testing records a distinct issue notifying you the problem may be resolved.

## Tags

Tags must be declared as static members in an extension on `Tag`:

```swift
extension Tag {
    @Tag static var critical: Self
    @Tag static var slow: Self
    @Tag static var networking: Self
    @Tag static var validation: Self
}

@Test(.tags(.critical, .networking))
func apiCallReturnsData() async throws { /* ... */ }
```

Filter tests by tag in Xcode test plans or CLI (tag-based filtering syntax varies by toolchain — verify for your Swift version).

## TestScoping and Test Organization

`TestScoping` consolidates per-test setup/teardown into reusable fixtures when attached through a custom trait:

```swift
struct DatabaseScope: TestTrait, SuiteTrait, TestScoping {
    func provideScope(
        for test: Test,
        testCase: Test.Case?,
        performing body: @Sendable () async throws -> Void
    ) async throws {
        let db = try await TestDatabase.create()
        do {
            try await body()
            try await db.destroy()
        } catch {
            try? await db.destroy()
            throw error
        }
    }
}

extension Trait where Self == DatabaseScope {
    static var databaseScope: Self { .init() }
}

@Test(.databaseScope, .tags(.database))
func insertsRecord() async throws {
    // Test runs inside DatabaseScope.provideScope
}
```
