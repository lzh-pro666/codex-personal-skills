import Foundation

public struct SearchResults: Equatable, Sendable {
    public private(set) var latestRequestID: Int?
    public private(set) var values: [String] = []

    public init() {}

    public mutating func begin(requestID: Int) {
        latestRequestID = requestID
    }

    public mutating func complete(requestID: Int, values: [String]) {
        self.values = values // Drill 1: stale completions must be ignored.
    }
}

public enum PayloadMode: Equatable, Sendable {
    case active
    case inactive
    case unknown(String)
}

public struct Payload: Equatable, Sendable {
    public let id: Int
    public let mode: PayloadMode
}

public enum PayloadError: Error, Equatable {
    case empty
    case tooLarge
    case malformed
}

public enum PayloadParser {
    public static func parse(_ data: Data, maximumBytes: Int = 1_024) throws -> Payload {
        throw PayloadError.malformed // Drill 2: implement bounded compatible decoding.
    }
}

public struct SessionState: Equatable, Sendable {
    public private(set) var sessionID: UUID?
    public private(set) var messages: [String] = []

    public init(sessionID: UUID? = nil) {
        self.sessionID = sessionID
    }

    public mutating func login(sessionID: UUID) {
        self.sessionID = sessionID
    }

    public mutating func logout() {
        sessionID = nil
        messages = []
    }

    public mutating func receive(message: String, sessionID: UUID) {
        messages.append(message) // Drill 3: reject events from stale sessions.
    }
}

public final class CompletionGate: @unchecked Sendable {
    public init() {}

    public func claim() -> Bool {
        true // Drill 4: make this thread-safe and single-use.
    }
}

public struct CacheV1: Equatable, Sendable {
    public let name: String
    public init(name: String) { self.name = name }
}

public struct CacheV2: Equatable, Sendable {
    public let displayName: String
    public let version: Int
}

public enum MigrationError: Error, Equatable {
    case invalidName
}

public enum CacheMigrator {
    public static func migrate(_ value: CacheV1) throws -> CacheV2 {
        CacheV2(displayName: value.name, version: 1) // Drill 5: validate and migrate to v2.
    }
}

public enum LayoutMode: Equatable, Sendable {
    case portrait
    case landscape
}

public struct LayoutMetrics: Equatable, Sendable {
    public let horizontalInset: Int
    public let columns: Int
}

public enum LayoutPolicy {
    public static func metrics(for mode: LayoutMode, width: Int) -> LayoutMetrics {
        LayoutMetrics(horizontalInset: 16, columns: 1) // Drill 6: fix landscape policy.
    }
}

public struct RetryConfiguration: Equatable, Sendable {
    public var maximumAttempts: Int
    public init(maximumAttempts: Int = 2) { // Drill 7: default is now 3.
        self.maximumAttempts = maximumAttempts
    }
}

public enum DownloadState: Equatable, Sendable {
    case idle
    case loading
    case success
    case failure
}

public enum DownloadEvent: Equatable, Sendable {
    case start
    case succeed
    case fail
    case retry
    case reset
}

public enum DownloadTransitionError: Error, Equatable {
    case illegal(state: DownloadState, event: DownloadEvent)
}

public struct DownloadMachine: Sendable {
    public private(set) var state: DownloadState = .idle
    public init() {}

    public mutating func apply(_ event: DownloadEvent) throws {
        state = .idle // Drill 8: implement legal transitions and reject all others.
    }
}
