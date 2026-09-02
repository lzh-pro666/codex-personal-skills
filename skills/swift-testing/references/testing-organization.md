# Test Organization and Review

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Test File Organization

```text
Tests/AppTests/          # Unit tests (Swift Testing or XCTest by target convention)
Tests/AppUITests/        # XCTest UI tests (Pages/, Flows/)
Tests/Fixtures/          # Test data (JSON, images)
Tests/Mocks/             # Shared mock implementations
```

Follow the repository's existing layout. When no convention exists, name test files `<TypeUnderTest>Tests.swift` and use behavior-revealing test names such as `fetchUserReturnsNilOnNetworkError()`.

### What to Test

**Prioritize when they belong to the contract:** business logic, validation rules, state transitions, error paths, empty/boundary input, async success/failure, and cancellation.

**Usually skip:** simple forwarding, Apple framework behavior, and private methods. Validate SwiftUI layout with an existing snapshot/UI strategy only when visual behavior is in scope.

## CustomTestStringConvertible

When parameterized test arguments appear in test output, Swift Testing uses `String(describing:)` by default. Conform to `CustomTestStringConvertible` for better output:

```swift
enum Food: CaseIterable {
    case paella, oden, ragu
}

extension Food: CustomTestStringConvertible {
    var testDescription: String {
        switch self {
        case .paella: "paella valenciana"
        case .oden: "おでん"
        case .ragu: "ragù alla bolognese"
        }
    }
}

@Test(arguments: Food.allCases)
func isDelicious(_ food: Food) { /* output shows custom descriptions */ }
```

Use this for any type passed as a parameterized test argument where the default description is unclear — especially enums, IDs, or model types.

## Availability-Conditional Tests

Use `@available` on test functions to run tests only on specific OS versions:

```swift
@Test
@available(iOS 18, macOS 15, *)
func usesNewAPI() async throws {
    let result = try await NewFramework.process()
    #expect(result.isValid)
}
```

Swift Testing skips `@available`-gated tests when running on older OS versions. This replaces XCTest's `#available` guard + early return pattern.

Do not put `@available` on a suite type or a type that contains a suite; Swift Testing requires suite types to always be available. Put availability gates on individual `@Test` functions instead.

## Common Mistakes and Review Checklist

1. **Testing implementation, not behavior.** Test what the code does, not how.
2. **No error path tests.** If a function can throw, test the throw path.
3. **Flaky async tests.** Use `confirmation` with expected counts, not `sleep` calls.
4. **Shared mutable state between tests.** Each test sets up its own state via `init()` in `@Suite` or a fixture.
5. **Missing accessibility identifiers in UI tests.** XCUITest queries rely on them.
6. **Not testing cancellation.** If cancellation is part of the contract, verify its observable result and cleanup.
7. **Unclear XCTest migration boundaries.** XCTest and Swift Testing can coexist; prefer separate files when that keeps imports, ownership, and runner expectations clearer.
8. **Non-Sendable helpers shared across tests.** Make shared concurrent helpers safe or keep them test-local.
9. **Assuming test order.** Parallel execution means declaration order and suite nesting do not create a workflow.
10. **Using `.serialized` as a dependency chain.** Serialized scopes avoid overlap; they do not pass state from one test to the next.

### Review Checklist

- [ ] The framework and assertions match the target's existing convention and required capabilities
- [ ] Test names describe behavior (`fetchUserReturnsNilOnNetworkError` not `testFetchUser`)
- [ ] Error paths have dedicated tests
- [ ] Async tests use `confirmation()`, not `Task.sleep`
- [ ] Parameterized tests used when repeated cases share setup and meaning
- [ ] Tags added only when the repository filters or groups by them
- [ ] Mocks conform to protocols, not subclass concrete types
- [ ] No shared mutable state between tests
- [ ] Tests do not rely on declaration order or shared suite instances
- [ ] `.serialized` is reserved for exclusive state, not workflow sequencing
- [ ] Cancellation tested for cancellable async operations
