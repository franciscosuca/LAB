import SwiftUI
import Foundation

/// A gradient card that embeds a live, interactive SwiftUI demo in a lesson.
struct DemoCard: View {
    let kind: DemoKind

    private var title: String {
        switch kind {
        case .greeter: return "String Interpolation, Live"
        case .styledText: return "The Modifiers Playground"
        case .stackLayout: return "The Stack Builder"
        case .counter: return "Your First Interactive App"
        case .colorMixer: return "Bindings & Sliders: Color Mixer"
        case .listNavigation: return "List + Navigation, Live"
        case .todoList: return "The To-Do App, Live"
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label(title, systemImage: "play.fill")
                .font(.headline)
                .foregroundStyle(.white)

            demo
                .padding(14)
                .background(.regularMaterial, in: .rect(cornerRadius: 12))

            Text("▶ This demo is real SwiftUI code running right now — the same techniques as in the lesson above.")
                .font(.caption)
                .foregroundStyle(.white.opacity(0.85))
        }
        .padding(16)
        .background(
            LinearGradient(colors: [.indigo, .purple],
                           startPoint: .topLeading,
                           endPoint: .bottomTrailing),
            in: .rect(cornerRadius: 16)
        )
    }

    @ViewBuilder
    private var demo: some View {
        switch kind {
        case .greeter: GreeterDemo()
        case .styledText: StyledTextDemo()
        case .stackLayout: StackLayoutDemo()
        case .counter: CounterDemo()
        case .colorMixer: ColorMixerDemo()
        case .listNavigation: ListNavigationDemo()
        case .todoList: TodoDemo()
        }
    }
}

// MARK: - Demo 1: Greeter (string interpolation)

struct GreeterDemo: View {
    @State private var name = ""

    private var code: String {
        """
        @State private var name = "\(name)"

        TextField("Your name", text: $name)
        Text("Hello, \\(name)! 👋")
        """
    }

    var body: some View {
        VStack(spacing: 12) {
            TextField("Type your name…", text: $name)
                .textFieldStyle(.roundedBorder)
                .frame(maxWidth: 300)

            Text(name.isEmpty ? "Hello, stranger! 👋" : "Hello, \(name)! 👋")
                .font(.title2)
                .bold()
                .animation(.default, value: name)

            CodeBlockView(code: code)
        }
    }
}

// MARK: - Demo 2: Styled text (modifiers)

struct StyledTextDemo: View {
    enum InkColor: String, CaseIterable, Identifiable {
        case purple, blue, green, orange, pink
        var id: String { rawValue }
        var color: Color {
            switch self {
            case .purple: return .purple
            case .blue: return .blue
            case .green: return .green
            case .orange: return .orange
            case .pink: return .pink
            }
        }
    }

    @State private var isBold = true
    @State private var isItalic = false
    @State private var ink: InkColor = .purple
    @State private var size: Double = 34

    private var styledText: Text {
        var text = Text("SwiftUI is fun")
        if isBold { text = text.bold() }
        if isItalic { text = text.italic() }
        return text
    }

    private var code: String {
        var lines = ["Text(\"SwiftUI is fun\")"]
        lines.append("    .font(.system(size: \(Int(size))))")
        if isBold { lines.append("    .bold()") }
        if isItalic { lines.append("    .italic()") }
        lines.append("    .foregroundStyle(.\(ink.rawValue))")
        return lines.joined(separator: "\n")
    }

    var body: some View {
        VStack(spacing: 12) {
            styledText
                .font(.system(size: size))
                .foregroundStyle(ink.color)
                .animation(.default, value: size)
                .frame(height: 70)

            HStack {
                Toggle("Bold", isOn: $isBold)
                Toggle("Italic", isOn: $isItalic)
                Picker("Color", selection: $ink) {
                    ForEach(InkColor.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
                .frame(maxWidth: 320)
                .labelsHidden()
            }

            HStack {
                Text("Size")
                Slider(value: $size, in: 20...60, step: 1)
                Text("\(Int(size))").monospacedDigit()
            }

            CodeBlockView(code: code)
        }
    }
}

// MARK: - Demo 3: Stack builder (layout)

struct StackLayoutDemo: View {
    enum Axis: String, CaseIterable, Identifiable {
        case vertical = "VStack", horizontal = "HStack"
        var id: String { rawValue }
    }
    enum AlignmentChoice: String, CaseIterable, Identifiable {
        case leading, center, trailing
        var id: String { rawValue }
    }

    @State private var axis: Axis = .vertical
    @State private var alignment: AlignmentChoice = .center
    @State private var spacing: Double = 12

    private var code: String {
        if axis == .vertical {
            return """
            VStack(alignment: .\(alignment.rawValue), spacing: \(Int(spacing))) {
                Text("One")
                Text("Two")
                Text("Three")
            }
            """
        }
        return """
        HStack(spacing: \(Int(spacing))) {
            Text("One")
            Text("Two")
            Text("Three")
        }
        """
    }

    private var horizontalAlignment: HorizontalAlignment {
        switch alignment {
        case .leading: return .leading
        case .center: return .center
        case .trailing: return .trailing
        }
    }

    private var chips: some View {
        Group {
            chip("One", .red)
            chip("Two", .orange)
            chip("Three", .green)
        }
    }

    private func chip(_ title: String, _ color: Color) -> some View {
        Text(title)
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(color.opacity(0.8), in: .capsule)
    }

    var body: some View {
        VStack(spacing: 12) {
            Picker("Direction", selection: $axis) {
                ForEach(Axis.allCases) { Text($0.rawValue).tag($0) }
            }
            .pickerStyle(.segmented)
            .labelsHidden()

            if axis == .vertical {
                Picker("Alignment", selection: $alignment) {
                    ForEach(AlignmentChoice.allCases) { Text($0.rawValue).tag($0) }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
            }

            HStack {
                Text("Spacing")
                Slider(value: $spacing, in: 0...40, step: 4)
                Text("\(Int(spacing))").monospacedDigit()
            }

            Group {
                if axis == .vertical {
                    VStack(alignment: horizontalAlignment, spacing: spacing) { chips }
                        .frame(maxWidth: .infinity)
                } else {
                    HStack(spacing: spacing) { chips }
                        .frame(maxWidth: .infinity)
                }
            }
            .frame(height: 150)
            .animation(.default, value: axis)
            .animation(.default, value: spacing)
            .animation(.default, value: alignment)

            CodeBlockView(code: code)
        }
    }
}

// MARK: - Demo 4: Counter (@State + Button)

struct CounterDemo: View {
    @State private var count = 0

    var body: some View {
        VStack(spacing: 12) {
            Text("Count: \(count)")
                .font(.system(size: 44, weight: .bold))
                .monospacedDigit()
                .contentTransition(.numericText())
                .animation(.default, value: count)

            HStack(spacing: 24) {
                Button { count -= 1 } label: {
                    Image(systemName: "minus.circle.fill").font(.title)
                }
                Button("Reset") { count = 0 }
                Button { count += 1 } label: {
                    Image(systemName: "plus.circle.fill").font(.title)
                }
            }
            .buttonStyle(.borderless)

            Text("Every tap changes @State, and SwiftUI redraws the text.")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
    }
}

// MARK: - Demo 5: Color mixer (bindings + sliders)

struct ColorMixerDemo: View {
    @State private var red = 0.30
    @State private var green = 0.55
    @State private var blue = 0.90

    private var color: Color { Color(red: red, green: green, blue: blue) }

    private var code: String {
        String(format: "Color(red: %.2f, green: %.2f, blue: %.2f)", red, green, blue)
    }

    private func slider(_ title: String, _ value: Binding<Double>, _ tint: Color) -> some View {
        HStack {
            Text(title)
                .frame(width: 46, alignment: .leading)
            Slider(value: value, in: 0...1)
                .tint(tint)
        }
    }

    var body: some View {
        VStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 12)
                .fill(color)
                .frame(height: 70)
                .animation(.default, value: color)

            slider("Red", $red, .red)
            slider("Green", $green, .green)
            slider("Blue", $blue, .blue)

            CodeBlockView(code: code)
        }
    }
}

// MARK: - Demo 6: List + navigation

struct DemoLanguage: Identifiable {
    let id = UUID()
    let name: String
    let emoji: String
    let fact: String
}

struct ListNavigationDemo: View {
    let languages = [
        DemoLanguage(name: "Swift", emoji: "🐦", fact: "Created at Apple in 2014."),
        DemoLanguage(name: "Rust", emoji: "🦀", fact: "Famous for memory safety."),
        DemoLanguage(name: "Python", emoji: "🐍", fact: "Named after Monty Python."),
        DemoLanguage(name: "Kotlin", emoji: "🎯", fact: "Popular for Android apps."),
    ]

    var body: some View {
        NavigationStack {
            List(languages) { language in
                NavigationLink {
                    VStack(spacing: 12) {
                        Text(language.emoji).font(.system(size: 64))
                        Text(language.fact).foregroundStyle(.secondary)
                    }
                    .padding()
                    .navigationTitle(language.name)
                } label: {
                    Text("\(language.emoji) \(language.name)")
                }
            }
            .navigationTitle("Languages")
        }
        .frame(height: 230)
        .clipShape(.rect(cornerRadius: 8))
    }
}

// MARK: - Demo 7: The capstone to-do app

struct DemoTask: Identifiable {
    let id = UUID()
    var title: String
    var isDone = false
}

struct TodoDemo: View {
    @State private var tasks = [
        DemoTask(title: "Add your own task below ⬇️"),
        DemoTask(title: "Tap the circle to complete me"),
        DemoTask(title: "Celebrate finishing the capstone 🎉", isDone: true),
    ]
    @State private var newTitle = ""

    private var canAdd: Bool {
        !newTitle.trimmingCharacters(in: .whitespaces).isEmpty
    }

    var body: some View {
        VStack(spacing: 0) {
            List {
                ForEach(tasks) { task in
                    HStack {
                        Button { toggle(task) } label: {
                            Image(systemName: task.isDone ? "checkmark.circle.fill" : "circle")
                                .foregroundStyle(task.isDone ? .green : .secondary)
                        }
                        .buttonStyle(.borderless)

                        Text(task.title)
                            .strikethrough(task.isDone)
                            .foregroundStyle(task.isDone ? .secondary : .primary)

                        Spacer()

                        Button { delete(task) } label: {
                            Image(systemName: "minus.circle")
                                .foregroundStyle(.red)
                        }
                        .buttonStyle(.borderless)
                    }
                }
            }
            .frame(minHeight: 140, maxHeight: 200)

            HStack {
                TextField("New task…", text: $newTitle)
                    .textFieldStyle(.roundedBorder)
                    .onSubmit(add)
                Button("Add", action: add)
                    .disabled(!canAdd)
            }
            .padding(10)
        }
        .clipShape(.rect(cornerRadius: 8))
    }

    private func add() {
        let title = newTitle.trimmingCharacters(in: .whitespaces)
        guard !title.isEmpty else { return }
        tasks.append(DemoTask(title: title))
        newTitle = ""
    }

    private func toggle(_ task: DemoTask) {
        guard let i = tasks.firstIndex(where: { $0.id == task.id }) else { return }
        tasks[i].isDone.toggle()
    }

    private func delete(_ task: DemoTask) {
        tasks.removeAll { $0.id == task.id }
    }
}
