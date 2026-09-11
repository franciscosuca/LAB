import Foundation

/// Tracks which lessons the learner has completed.
/// Persisted to `UserDefaults` so progress survives app restarts.
final class ProgressStore: ObservableObject {
    @Published private(set) var completedIDs: Set<String>

    private let storageKey = "com.swiftschool.completedLessons"

    init() {
        completedIDs = Set(UserDefaults.standard.stringArray(forKey: storageKey) ?? [])
    }

    func isCompleted(_ lesson: Lesson) -> Bool {
        completedIDs.contains(lesson.id)
    }

    func toggle(_ lesson: Lesson) {
        if completedIDs.contains(lesson.id) {
            completedIDs.remove(lesson.id)
        } else {
            completedIDs.insert(lesson.id)
        }
        UserDefaults.standard.set(Array(completedIDs), forKey: storageKey)
    }

    var totalCompleted: Int { completedIDs.count }
}
