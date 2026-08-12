---
name: swift-testing
description: Write, migrate, or review Swift unit tests using Swift Testing or XCTest. Use for @Test, @Suite, #expect, #require, async tests, parameterization, test isolation, XCTest migration, or choosing framework boundaries; do not trigger for production-code changes that do not involve tests.
---

# Swift Testing

Write behavior-focused, deterministic tests that match the affected target's existing framework and toolchain. Do not migrate XCTest merely to modernize syntax.

## Workflow

1. Identify the behavior, failure mode, and target under test.
2. Inspect nearby tests, imports, test-plan settings, Swift version, and available SDK before choosing APIs.
3. Use Swift Testing for new unit tests when the target already supports it; preserve XCTest/XCUITest for UI automation, performance tests, existing snapshot tooling, Objective-C exception cases, or incremental migrations.
4. Isolate fixtures and external state. Swift Testing runs tests in parallel by default; use serialization only for truly shared resources, never to encode test order.
5. Run the narrowest repository test command and report any unverified boundary.

## Core Rules

- Assert observable behavior, not private implementation details.
- Use `#require` when later checks depend on an unwrapped or validated value; use `#expect` for independent expectations.
- Replace unconditional `XCTFail` with `Issue.record` only when the target supports the intended Swift Testing API.
- Prefer parameterized cases for repeated inputs and `confirmation` or injected clocks over sleeps for async behavior.
- Cover error, cancellation, empty, and boundary paths when they are part of the changed contract.
- Do not share mutable globals across parallel tests. Keep mocks protocol-based when the production boundary already supports injection.
- Gate exit testing, capture lists, attachment APIs, cancellation APIs, and cross-framework interoperability by the actual compiler/runtime rather than remembered availability.

## Load References Only When Needed

- Parameterized suites, tags, complex confirmation semantics, mocking design, or XCTest migration: `references/testing-patterns.md`
- Exit tests, warnings, cancellation, attachments, and version-gated APIs: `references/testing-advanced.md`

Do not load a reference for a normal behavior test, a controlled async fake, or a straightforward `#expect`/`#require` conversion when the skill and nearby tests already provide enough guidance.

## Completion Check

- The test fails for the intended regression and passes for the corrected behavior where practical.
- It is deterministic under parallel execution and does not rely on declaration order or arbitrary delays.
- Framework/API choices match the target and repository conventions.
- The focused test command passes, or the exact verification gap is reported.
