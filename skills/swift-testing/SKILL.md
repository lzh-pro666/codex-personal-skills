---
name: swift-testing
description: Write, migrate, or review Swift unit tests using Swift Testing or XCTest. Use for @Test, @Suite, expectations, async tests, parameterization, isolation, XCTest migration, or framework-boundary decisions; not production-only changes.
---

# Swift Testing

Write deterministic, behavior-focused tests that match the target's existing framework and toolchain. Do not migrate XCTest solely to modernize syntax.

## Decisions

- Identify the observable behavior, failure mode, target, nearby conventions, test-plan settings, Swift version, and SDK.
- Prefer Swift Testing for new unit tests when the target supports it. Keep XCTest/XCUITest where UI automation, performance, snapshots, Objective-C exceptions, or incremental migration require it.
- Use `#require` when later assertions depend on a value; use `#expect` for independent expectations.
- Prefer parameterization for repeated inputs and confirmations, injected clocks, virtual time, or completion signals over sleeps.
- Isolate fixtures and external state. Parallel execution must not share mutable globals or depend on declaration order; serialize only truly exclusive resources.
- Test errors, cancellation, empty input, and boundaries when they belong to the contract. Use protocol-based doubles when the production boundary already supports injection.

## References

- Suites, parameterization, confirmations, tags, or scoping: `references/testing-core.md`
- XCTest migration, test doubles, or testable boundaries: `references/testing-migration-doubles.md`
- Async/concurrent tests, XCUITest, performance, or snapshots: `references/testing-async-ui.md`
- File organization, availability, argument descriptions, or review: `references/testing-organization.md`
- Warnings, cancellation APIs, exit tests, attachments, or version gates: `references/testing-advanced.md`

Use `references/testing-patterns.md` only as a router for a mixed testing request.

Run the narrowest authorized repository test command. Report whether the intended regression was demonstrated, whether corrected behavior passed, and any toolchain or runtime gap.
