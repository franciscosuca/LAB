import SwiftUI

/// The root UI: a sidebar with modules & lessons, and a detail pane.
struct ContentView: View {
    @EnvironmentObject private var progress: ProgressStore
    @State private var selection: Lesson?

    var body: some View {
        NavigationSplitView {
            List(selection: $selection) {
                Label("Home", systemImage: "house.fill")
                    .tag(nil as Lesson?)

                ForEach(Curriculum.modules) { module in
                    Section {
                        ForEach(module.lessons) { lesson in
                            LessonRow(
                                lesson: lesson,
                                isCompleted: progress.isCompleted(lesson)
                            )
                            .tag(lesson)
                        }
                    } header: {
                        Label(module.title, systemImage: module.icon)
                    }
                }
            }
            .navigationTitle("SwiftSchool")
            .frame(minWidth: 260)
        } detail: {
            if let selection {
                LessonDetailView(lesson: selection)
            } else {
                WelcomeView(onStart: startLearning)
            }
        }
    }

    /// Jump to the first not-yet-completed lesson.
    private func startLearning() {
        let lessons = Curriculum.allLessons
        selection = lessons.first { !progress.isCompleted($0) } ?? lessons.first
    }
}

/// The landing screen shown when no lesson is selected.
struct WelcomeView: View {
    @EnvironmentObject private var progress: ProgressStore
    let onStart: () -> Void

    private var totalLessons: Int { Curriculum.allLessons.count }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            Image(systemName: "swift")
                .font(.system(size: 72))
                .foregroundStyle(.orange.gradient)

            Text("SwiftSchool")
                .font(.system(size: 44, weight: .bold))

            Text("Learn to build iOS & Mac apps — interactively.")
                .font(.title3)
                .foregroundStyle(.secondary)

            HStack(spacing: 20) {
                FeatureCard(icon: "book.fill",
                            title: "10 Guided Lessons",
                            text: "From Swift basics to real app architecture")
                FeatureCard(icon: "play.fill",
                            title: "7 Live Demos",
                            text: "Real, running SwiftUI code you can touch")
                FeatureCard(icon: "checkmark.circle.fill",
                            title: "Quizzes & Progress",
                            text: "Test yourself and track completion")
            }

            if progress.totalCompleted > 0 {
                VStack(spacing: 6) {
                    ProgressView(value: Double(progress.totalCompleted),
                                 total: Double(totalLessons))
                        .frame(maxWidth: 320)
                    Text("\(progress.totalCompleted) of \(totalLessons) lessons complete")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            Button(action: onStart) {
                Label(progress.totalCompleted > 0 ? "Continue Learning" : "Start Learning",
                      systemImage: "arrow.right.circle.fill")
                    .font(.headline)
            }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)

            Spacer()
        }
        .padding(40)
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

private struct FeatureCard: View {
    let icon: String
    let title: String
    let text: String

    var body: some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title)
                .foregroundStyle(.tint)
            Text(title)
                .font(.headline)
            Text(text)
                .font(.caption)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
        }
        .padding()
        .frame(width: 190, height: 130)
        .background(.regularMaterial, in: .rect(cornerRadius: 12))
    }
}
