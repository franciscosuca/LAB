// swift-tools-version: 6.1
import PackageDescription

let package = Package(
    name: "SwiftSchool",
    platforms: [.macOS(.v13)],
    targets: [
        .executableTarget(
            name: "SwiftSchool",
            path: "Sources/SwiftSchool"
        )
    ]
)
