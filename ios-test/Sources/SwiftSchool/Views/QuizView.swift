import SwiftUI

/// An interactive multiple-choice quiz shown at the end of a lesson.
struct QuizView: View {
    let questions: [QuizQuestion]

    /// questionIndex -> chosen optionIndex
    @State private var selections: [Int: Int] = [:]

    private var answeredAll: Bool { selections.count == questions.count }

    private var score: Int {
        questions.indices.count { selections[$0] == questions[$0].correctIndex }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Label("Quick Quiz", systemImage: "questionmark.bubble.fill")
                .font(.title2)
                .bold()

            ForEach(Array(questions.enumerated()), id: \.offset) { index, question in
                QuestionCard(
                    question: question,
                    selection: selections[index],
                    onChoose: { choice in
                        withAnimation(.default) { selections[index] = choice }
                    }
                )
            }

            if answeredAll {
                HStack {
                    if score == questions.count {
                        Label("Perfect score — \(score)/\(questions.count)! 🎉",
                              systemImage: "star.fill")
                            .foregroundStyle(.green)
                    } else {
                        Label("You scored \(score)/\(questions.count). Review the lesson and try again!",
                              systemImage: "arrow.counterclockwise")
                            .foregroundStyle(.orange)
                        Button("Retry") {
                            withAnimation(.default) { selections = [:] }
                        }
                    }
                }
                .padding()
                .background(.quaternary, in: .rect(cornerRadius: 10))
            }
        }
        .padding()
        .background(.quaternary.opacity(0.35), in: .rect(cornerRadius: 16))
    }
}

private struct QuestionCard: View {
    let question: QuizQuestion
    let selection: Int?
    let onChoose: (Int) -> Void

    private func icon(for index: Int) -> String {
        guard let selection else { return "circle" }
        if index == question.correctIndex { return "checkmark.circle.fill" }
        if index == selection { return "xmark.circle.fill" }
        return "circle"
    }

    private func iconColor(for index: Int) -> Color {
        guard let selection else { return .secondary }
        if index == question.correctIndex { return .green }
        if index == selection { return .red }
        return .secondary
    }

    private func background(for index: Int) -> Color {
        guard let selection else { return .primary.opacity(0.05) }
        if index == question.correctIndex { return .green.opacity(0.18) }
        if index == selection { return .red.opacity(0.15) }
        return .clear
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            Text(question.question)
                .font(.headline)

            ForEach(Array(question.options.enumerated()), id: \.offset) { index, option in
                Button { onChoose(index) } label: {
                    HStack {
                        Image(systemName: icon(for: index))
                            .foregroundStyle(iconColor(for: index))
                        Text(option)
                            .foregroundStyle(.primary)
                        Spacer()
                    }
                    .padding(10)
                    .background(background(for: index), in: .rect(cornerRadius: 8))
                }
                .buttonStyle(.plain)
                .disabled(selection != nil)
            }

            if selection != nil {
                Text(question.explanation)
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.regularMaterial, in: .rect(cornerRadius: 12))
    }
}
