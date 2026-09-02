# Accessibility Testing

These examples are loaded only for this surface. Confirm repository conventions, deployment target, and installed toolchain before adapting them.

## Automated Accessibility Testing

Use `XCUIElement` attributes to verify accessibility properties in UI tests.

### Verifying Labels and Identifiers

```swift
func testAccessibilityLabels() throws {
    let app = XCUIApplication()
    app.launch()

    // Verify buttons have meaningful labels
    let settingsButton = app.buttons["Settings"]
    XCTAssertTrue(settingsButton.exists, "Settings button must exist")
    XCTAssertTrue(settingsButton.isEnabled, "Settings button must be enabled")

    // Verify a cell groups content correctly
    let productCell = app.cells.element(boundBy: 0)
    XCTAssertFalse(productCell.label.isEmpty, "Product cell must have a combined label")
}
```

### Testing Focus and Selection State

```swift
func testTabNavigationOrder() throws {
    let app = XCUIApplication()
    app.launch()

    let usernameField = app.textFields["Username"]
    let passwordField = app.secureTextFields["Password"]

    usernameField.tap()
    XCTAssertTrue(usernameField.hasFocus)

    // Tab to next field
    usernameField.typeText("\t")
    XCTAssertTrue(passwordField.hasFocus)
}
```

### Testing Custom Actions

```swift
func testSwipeToDeleteAlternative() throws {
    let app = XCUIApplication()
    app.launch()

    let cell = app.cells["task-buy-groceries"]
    XCTAssertTrue(cell.exists)

    // Verify accessibility identifier is set for test targeting
    XCTAssertEqual(cell.identifier, "task-buy-groceries")
}
```
