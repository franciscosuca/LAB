import Foundation

/// A learning module: a group of lessons (like a chapter in a book).
struct Module: Identifiable, Hashable {
    let id: String
    let title: String
    let icon: String // SF Symbol name
    let lessons: [Lesson]
}

/// One lesson: a sequence of content blocks plus a quiz.
struct Lesson: Identifiable, Hashable {
    let id: String
    let title: String
    let subtitle: String
    let minutes: Int
    let blocks: [LessonBlock]
    let quiz: [QuizQuestion]
}

/// Lessons are built from these building blocks — this enum IS the
/// rendering engine of the app (see `LessonBlockView`).
enum LessonBlock: Hashable {
    case heading(String)
    case text(String)
    case code(String)
    case tip(String)
    case challenge(String)
    case demo(DemoKind)
}

/// Which interactive demo a lesson embeds.
enum DemoKind: String, Hashable {
    case greeter
    case styledText
    case stackLayout
    case counter
    case colorMixer
    case listNavigation
    case todoList
}

/// A multiple-choice quiz question.
struct QuizQuestion: Hashable {
    let question: String
    let options: [String]
    let correctIndex: Int
    let explanation: String
}
