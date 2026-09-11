import SwiftUI

/// The entry point of the app.
/// Every SwiftUI app starts with a struct marked `@main` that conforms to `App`,
/// and returns a `Scene` — on desktop, usually a `WindowGroup`.
@main
struct SwiftSchoolApp: App {
    /// One shared progress store for the whole app (saved to UserDefaults).
    @StateObject private var progress = ProgressStore()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(progress)
                .frame(minWidth: 940, minHeight: 620)
        }
        .defaultSize(width: 1120, height: 760)
        .windowResizability(.contentMinSize)
    }
}
