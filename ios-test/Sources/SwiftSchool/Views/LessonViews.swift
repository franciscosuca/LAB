import SwiftUI

/// Renders **bold** and `code` markdown found in lesson text.
func markdownText(_ string: String) -> Text {
    let options = AttributedString.MarkdownParsingOptions(
        interpretedSyntax: .inlineOnlyPreservingWhitespace
    )
    if let attributed = try? AttributedString(markdown: string, options: options) {
        return Text(attributed)
    }
    return Text(string)
}

/// The full lesson page: header, content blocks, quiz, completion button.
struct LessonDetailView: View {
    @EnvironmentObject private var progress: ProgressStore
    let lesson: Lesson

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                VStack(alignment: .leading, spacing: 8) {
                    Text(lesson.subtitle)
                        .font(.title3)
                        .foregroundStyle(.secondary)
                    Label("\(lesson.minutes) minute lesson", systemImage: "clock")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Divider()

                ForEach(Array(lesson.blocks.enumerated()), id: \.offset) { _, block in
                    LessonBlockView(block: block)
                }

                if !lesson.quiz.isEmpty {
                    Divider()
                    QuizView(questions: lesson.quiz)
                }

                Divider()

                completionButton
            }
            .padding(32)
            .frame(maxWidth: 780, alignment: .leading)
            .frame(maxWidth: .infinity)
        }
        .navigationTitle(lesson.title)
    }

    private var completionButton: some View {
        let done = progress.isCompleted(lesson)
        return Button {
            withAnimation(.default) { progress.toggle(lesson) }
        } label: {
            Label(
                done ? "Completed ✓ (tap to undo)" : "Mark lesson as complete",
                systemImage: done ? "checkmark.circle.fill" : "circle"
            )
        }
        .buttonStyle(.borderedProminent)
        .tint(done ? Color.green : nil)
        .controlSize(.large)
    }
}

/// Renders a single lesson block — this switch is what turns
/// the `Curriculum` data into UI.
struct LessonBlockView: View {
    let block: LessonBlock

    var body: some View {
        switch block {
        case .heading(let text):
            Text(text)
                .font(.title2)
                .bold()
                .padding(.top, 8)
        case .text(let text):
            markdownText(text)
                .lineSpacing(4)
        case .code(let code):
            CodeBlockView(code: code)
        case .tip(let text):
            CalloutCard(icon: "lightbulb.fill", title: "Tip", color: .yellow, text: text)
        case .challenge(let text):
            CalloutCard(icon: "flag.fill", title: "Challenge", color: .purple, text: text)
        case .demo(let kind):
            DemoCard(kind: kind)
        }
    }
}

/// A small colored callout used for tips and challenges.
struct CalloutCard: View {
    let icon: String
    let title: String
    let color: Color
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundStyle(color)
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.headline)
                markdownText(text).font(.callout)
            }
        }
        .padding()
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(color.opacity(0.12), in: .rect(cornerRadius: 12))
    }
}

/// One row in the sidebar lesson list.
struct LessonRow: View {
    let lesson: Lesson
    let isCompleted: Bool

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: isCompleted ? "checkmark.circle.fill" : "circle")
                .foregroundStyle(isCompleted ? .green : .secondary)
            VStack(alignment: .leading, spacing: 2) {
                Text(lesson.title)
                Text("\(lesson.minutes) min")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.vertical, 2)
    }
}
