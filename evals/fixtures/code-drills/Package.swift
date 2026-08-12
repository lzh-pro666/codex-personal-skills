// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "CodeQualityDrills",
    platforms: [.macOS(.v13)],
    products: [.library(name: "CodeQualityDrills", targets: ["CodeQualityDrills"])],
    targets: [
        .target(name: "CodeQualityDrills"),
        .testTarget(name: "CodeQualityDrillsTests", dependencies: ["CodeQualityDrills"]),
    ]
)
