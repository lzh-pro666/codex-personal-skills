import Foundation
import Dispatch
import Testing
@testable import CodeQualityDrills

private final class AsyncSignal: @unchecked Sendable {
    private let lock = NSLock()
    private var fired = false
    private var waiters: [CheckedContinuation<Void, Never>] = []

    func fire() {
        lock.lock()
        guard !fired else {
            lock.unlock()
            return
        }
        fired = true
        let pending = waiters
        waiters.removeAll()
        lock.unlock()
        pending.forEach { $0.resume() }
    }

    func wait() async {
        await withCheckedContinuation { continuation in
            lock.lock()
            if fired {
                lock.unlock()
                continuation.resume()
            } else {
                waiters.append(continuation)
                lock.unlock()
            }
        }
    }
}

private final class FakeAvatarUploadTask: AvatarUploadTask, @unchecked Sendable {
    private let lock = NSLock()
    private var cancellations = 0

    var cancellationCount: Int {
        lock.lock()
        defer { lock.unlock() }
        return cancellations
    }

    func cancel() {
        lock.lock()
        cancellations += 1
        lock.unlock()
    }
}

private final class ControllableAvatarUploadTransport: AvatarUploadTransport, @unchecked Sendable {
    let task = FakeAvatarUploadTask()
    let started = AsyncSignal()

    private let lock = NSLock()
    private var completion: (@Sendable (Result<String, any Error>) -> Void)?

    func startUpload(
        data: Data,
        completion: @escaping @Sendable (Result<String, any Error>) -> Void
    ) -> any AvatarUploadTask {
        lock.lock()
        self.completion = completion
        lock.unlock()
        started.fire()
        return task
    }

    func complete(_ result: Result<String, any Error>) {
        lock.lock()
        let callback = completion
        lock.unlock()
        callback?(result)
    }
}

private final class DelayedReturnAvatarUploadTransport: AvatarUploadTransport, @unchecked Sendable {
    let task = FakeAvatarUploadTask()
    let started = AsyncSignal()
    private let mayReturn = DispatchSemaphore(value: 0)

    func startUpload(
        data: Data,
        completion: @escaping @Sendable (Result<String, any Error>) -> Void
    ) -> any AvatarUploadTask {
        started.fire()
        mayReturn.wait()
        return task
    }

    func allowTaskHandleToReturn() {
        mayReturn.signal()
    }
}

private enum StubUploadError: Error {
    case failed
}

private enum StubWriteError: Error, Equatable {
    case denied
}

private struct FailingCacheAtomicWriter: CacheAtomicWriting {
    func replace(data: Data, at url: URL) throws {
        throw StubWriteError.denied
    }
}

struct TransitionCase: Sendable {
    let start: DownloadState
    let event: DownloadEvent
    let end: DownloadState
}

struct IllegalTransitionCase: Sendable {
    let start: DownloadState
    let event: DownloadEvent
}

private func downloadMachine(in state: DownloadState) throws -> DownloadMachine {
    var machine = DownloadMachine()
    switch state {
    case .idle:
        break
    case .loading:
        try machine.apply(.start)
    case .success:
        try machine.apply(.start)
        try machine.apply(.succeed)
    case .failure:
        try machine.apply(.start)
        try machine.apply(.fail)
    }
    return machine
}

@Test("latest search completion wins")
func latestSearchCompletionWins() {
    var results = SearchResults()
    results.begin(requestID: 1)
    results.begin(requestID: 2)
    results.complete(requestID: 2, values: ["new"])
    results.complete(requestID: 1, values: ["stale"])
    #expect(results.values == ["new"])
}

@Test("starting a new search cancels the previous Task")
@MainActor
func newSearchCancelsPreviousTask() async {
    let oldStarted = AsyncSignal()
    let oldCancelled = AsyncSignal()
    let viewModel = SearchViewModel { query in
        guard query == "old" else { return ["new"] }
        oldStarted.fire()
        return await withTaskCancellationHandler {
            do {
                try await Task.sleep(nanoseconds: 60_000_000_000)
                return ["unexpected"]
            } catch {
                return ["old-after-cancel"]
            }
        } onCancel: {
            oldCancelled.fire()
        }
    }

    viewModel.search("old")
    await oldStarted.wait()
    viewModel.search("new")
    await oldCancelled.wait()
    await viewModel.waitForCurrentSearch()

    #expect(viewModel.values == ["new"])
}

@Test("payload parser boundaries")
func payloadParserBoundaries() throws {
    #expect(throws: PayloadError.empty) { try PayloadParser.parse(Data()) }
    #expect(throws: PayloadError.tooLarge) { try PayloadParser.parse(Data(repeating: 0, count: 5), maximumBytes: 4) }
    let unknown = try PayloadParser.parse(Data(#"{"id":7,"mode":"future"}"#.utf8))
    #expect(unknown == Payload(id: 7, mode: .unknown("future")))
}

@Test("logged-out state rejects stale session events")
func staleSessionEventIsRejected() {
    let oldSession = UUID()
    var state = SessionState(sessionID: oldSession)
    state.logout()
    state.receive(message: "stale", sessionID: oldSession)
    #expect(state.messages.isEmpty)
}

@Test("completion gate has one winner")
func completionGateHasOneWinner() async {
    let gate = CompletionGate()
    let winners = await withTaskGroup(of: Bool.self, returning: Int.self) { group in
        for _ in 0..<64 { group.addTask { gate.claim() } }
        var count = 0
        for await won in group where won { count += 1 }
        return count
    }
    #expect(winners == 1)
}

@Test("cancelling avatar upload cancels underlying work and resumes with cancellation")
func cancellingAvatarUploadCancelsUnderlyingWork() async {
    let transport = ControllableAvatarUploadTransport()
    let service = AvatarUploadService(transport: transport)
    let upload = Task { try await service.upload(Data([1, 2, 3])) }

    await transport.started.wait()
    upload.cancel()

    do {
        _ = try await upload.value
        Issue.record("cancelled upload unexpectedly succeeded")
    } catch let error as AvatarUploadError {
        #expect(error == .cancelled)
    } catch {
        Issue.record("cancelled upload threw unexpected error: \(error)")
    }
    #expect(transport.task.cancellationCount == 1)
}

@Test("cancellation before transport returns its handle still cancels that handle")
func cancellationBeforeUploadHandleReturns() async {
    let transport = DelayedReturnAvatarUploadTransport()
    let service = AvatarUploadService(transport: transport)
    let upload = Task { try await service.upload(Data([9])) }

    await transport.started.wait()
    upload.cancel()
    transport.allowTaskHandleToReturn()

    do {
        _ = try await upload.value
        Issue.record("cancelled upload unexpectedly succeeded")
    } catch let error as AvatarUploadError {
        #expect(error == .cancelled)
    } catch {
        Issue.record("cancelled upload threw unexpected error: \(error)")
    }
    #expect(transport.task.cancellationCount == 1)
}

@Test("avatar upload maps transport errors")
func avatarUploadMapsTransportErrors() async {
    let transport = ControllableAvatarUploadTransport()
    let service = AvatarUploadService(transport: transport)
    let upload = Task { try await service.upload(Data([4])) }

    await transport.started.wait()
    transport.complete(.failure(StubUploadError.failed))

    do {
        _ = try await upload.value
        Issue.record("failed upload unexpectedly succeeded")
    } catch let error as AvatarUploadError {
        #expect(error == .transportFailure)
    } catch {
        Issue.record("upload threw an unmapped error: \(error)")
    }
}

@Test("avatar upload cancellation and callbacks resolve continuation once")
func avatarUploadCancellationAndCallbacksResolveOnce() async {
    let transport = ControllableAvatarUploadTransport()
    let service = AvatarUploadService(transport: transport)
    let upload = Task { try await service.upload(Data([5, 6])) }

    await transport.started.wait()
    await withTaskGroup(of: Void.self) { group in
        group.addTask { transport.complete(.success("avatar://new")) }
        group.addTask { upload.cancel() }
    }

    do {
        let value = try await upload.value
        #expect(value == "avatar://new")
    } catch let error as AvatarUploadError {
        #expect(error == .cancelled)
    } catch {
        Issue.record("race resolved with unexpected error: \(error)")
    }

    // A broken bridge double-resumes its checked continuation on this late callback.
    transport.complete(.failure(StubUploadError.failed))
    #expect(transport.task.cancellationCount <= 1)
}

@Test("cache migration validates and produces v2")
func cacheMigration() throws {
    #expect(throws: MigrationError.invalidName) { try CacheMigrator.migrate(CacheV1(name: "   ")) }
    #expect(try CacheMigrator.migrate(CacheV1(name: "  Ada  ")) == CacheV2(displayName: "Ada", version: 2))
}

@Test("cache migration atomically replaces persisted v1 with v2")
func cacheMigrationAtomicallyReplacesPersistedValue() throws {
    let url = FileManager.default.temporaryDirectory
        .appendingPathComponent("cache-\(UUID().uuidString).json")
    defer { try? FileManager.default.removeItem(at: url) }
    let store = FileCacheStore(url: url)

    try store.saveV1(CacheV1(name: "  Ada  "))
    let migrated = try store.migrateToLatest()

    #expect(migrated == CacheV2(displayName: "Ada", version: 2))
    #expect(try store.load() == .v2(CacheV2(displayName: "Ada", version: 2)))
}

@Test("failed cache replacement preserves persisted v1 bytes")
func failedCacheReplacementPreservesOldVersion() throws {
    let url = FileManager.default.temporaryDirectory
        .appendingPathComponent("cache-\(UUID().uuidString).json")
    defer { try? FileManager.default.removeItem(at: url) }
    let initialStore = FileCacheStore(url: url)
    try initialStore.saveV1(CacheV1(name: "Ada"))
    let originalBytes = try Data(contentsOf: url)
    let failingStore = FileCacheStore(url: url, writer: FailingCacheAtomicWriter())

    #expect(throws: StubWriteError.denied) {
        try failingStore.migrateToLatest()
    }

    #expect(try Data(contentsOf: url) == originalBytes)
    #expect(try initialStore.load() == .v1(CacheV1(name: "Ada")))
}

@Test("landscape layout uses two columns with safe inset")
func landscapeLayout() {
    #expect(LayoutPolicy.metrics(for: .portrait, width: 390) == LayoutMetrics(horizontalInset: 16, columns: 1))
    #expect(LayoutPolicy.metrics(for: .landscape, width: 844) == LayoutMetrics(horizontalInset: 24, columns: 2))
}

@Test("layout transition deactivates portrait constraints before landscape constraints")
func landscapeConstraintTransition() {
    #expect(
        LayoutConstraintPolicy.transition(from: .portrait, to: .landscape)
            == LayoutConstraintTransition(deactivate: .portrait, activate: .landscape)
    )
    #expect(
        LayoutConstraintPolicy.transition(from: .landscape, to: .landscape)
            == LayoutConstraintTransition(deactivate: nil, activate: nil)
    )
}

@Test("retry default changes without overriding explicit values")
func retryDefault() {
    #expect(RetryConfiguration().maximumAttempts == 3)
    #expect(RetryConfiguration(maximumAttempts: 5).maximumAttempts == 5)
}

@Test("retry configuration loader defaults missing values and preserves explicit override")
func retryConfigurationLoading() throws {
    #expect(try RetryConfigurationLoader.load(from: nil).maximumAttempts == 3)
    #expect(try RetryConfigurationLoader.load(from: Data("{}".utf8)).maximumAttempts == 3)
    #expect(
        try RetryConfigurationLoader.load(from: Data(#"{"maximumAttempts":5}"#.utf8)).maximumAttempts == 5
    )
}

@Test("download state machine accepts legal path")
func downloadLegalTransitions() throws {
    var machine = DownloadMachine()
    try machine.apply(.start)
    #expect(machine.state == .loading)
    try machine.apply(.fail)
    #expect(machine.state == .failure)
    try machine.apply(.retry)
    #expect(machine.state == .loading)
    try machine.apply(.succeed)
    #expect(machine.state == .success)
    try machine.apply(.reset)
    #expect(machine.state == .idle)
}

@Test("download state machine rejects illegal event")
func downloadIllegalTransition() {
    var machine = DownloadMachine()
    #expect(throws: DownloadTransitionError.illegal(state: .idle, event: .succeed)) {
        try machine.apply(.succeed)
    }
}

@Test(
    "download state machine parameterizes every legal transition",
    arguments: [
        TransitionCase(start: .idle, event: .start, end: .loading),
        TransitionCase(start: .loading, event: .succeed, end: .success),
        TransitionCase(start: .loading, event: .fail, end: .failure),
        TransitionCase(start: .failure, event: .retry, end: .loading),
        TransitionCase(start: .failure, event: .reset, end: .idle),
        TransitionCase(start: .success, event: .reset, end: .idle),
    ]
)
func everyLegalDownloadTransition(testCase: TransitionCase) throws {
    var machine = try downloadMachine(in: testCase.start)
    try machine.apply(testCase.event)
    #expect(machine.state == testCase.end)
}

@Test(
    "download state machine rejects representative illegal transitions without mutation",
    arguments: [
        IllegalTransitionCase(start: .idle, event: .succeed),
        IllegalTransitionCase(start: .idle, event: .retry),
        IllegalTransitionCase(start: .loading, event: .start),
        IllegalTransitionCase(start: .success, event: .retry),
        IllegalTransitionCase(start: .failure, event: .succeed),
    ]
)
func illegalDownloadTransitionsPreserveState(testCase: IllegalTransitionCase) throws {
    var machine = try downloadMachine(in: testCase.start)
    #expect(throws: DownloadTransitionError.illegal(state: testCase.start, event: testCase.event)) {
        try machine.apply(testCase.event)
    }
    #expect(machine.state == testCase.start)
}
