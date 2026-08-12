// swift-tools-version: 6.0

import PackageDescription

let package = Package(
    name: "ReducerRedHarness",
    platforms: [.macOS(.v14)],
    products: [
        .library(name: "CodeQualityDrills", targets: ["CodeQualityDrills"]),
    ],
    targets: [
        .target(name: "CodeQualityDrills"),
        .testTarget(name: "ReducerRedTests", dependencies: ["CodeQualityDrills"]),
    ]
)
