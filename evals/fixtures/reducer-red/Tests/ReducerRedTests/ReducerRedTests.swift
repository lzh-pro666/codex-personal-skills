import Foundation
import Testing
@testable import CodeQualityDrills

@Test("logged-out state rejects stale session events")
func loggedOutStateRejectsStaleSessionEvents() {
    let staleSessionID = UUID()
    var state = SessionState(sessionID: staleSessionID)

    state.logout()
    state.receive(message: "stale", sessionID: staleSessionID)

    #expect(state.messages.isEmpty)
}
