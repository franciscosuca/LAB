import Foundation

/// All learning content in the app. This file is deliberately data-driven:
/// lessons are just values of `Lesson`, built from `LessonBlock`s.
enum Curriculum {

    static let modules: [Module] = [
        Module(
            id: "foundations",
            title: "Swift Foundations",
            icon: "swift",
            lessons: [howAppsWork, variablesAndTypes, functionsAndOptionals]
        ),
        Module(
            id: "swiftui",
            title: "SwiftUI Essentials",
            icon: "paintpalette.fill",
            lessons: [firstView, stacks, stateAndInteraction, listsAndNavigation]
        ),
        Module(
            id: "build",
            title: "Build Real Things",
            icon: "hammer.fill",
            lessons: [dataAndModels, capstoneTodo, nextSteps]
        ),
    ]

    static var allLessons: [Lesson] { modules.flatMap(\.lessons) }

    // MARK: - Module 1: Swift Foundations

    static let howAppsWork = Lesson(
        id: "swift-01-how-apps-work",
        title: "How Apps Work",
        subtitle: "What an app really is — and the two tools you'll master: Swift & SwiftUI.",
        minutes: 5,
        blocks: [
            .text("Every app you've ever used — from Messages to your favorite game — is a set of **instructions** written by a programmer in a *programming language*. For Apple devices, that language is **Swift**."),
            .text("You write Swift **code** (plain text). A tool called the **compiler** translates it into the 1s and 0s your device understands. The part of an app you see and touch — buttons, lists, text — is the **user interface (UI)**, and on Apple platforms we build UIs with a framework called **SwiftUI**."),
            .code("""
            import SwiftUI

            struct ContentView: View {
                var body: some View {
                    Text("Hello, world!")
                }
            }
            """),
            .text("That tiny program is a complete screen! **SwiftUI is declarative**: instead of giving step-by-step orders (\"draw a label at x:100, y:200\"), you *describe what the UI should look like*, and SwiftUI figures out how to draw it — and redraw it whenever your data changes."),
            .text("You are reading this inside an app built exactly this way. Every screen, button and demo here is Swift & SwiftUI."),
            .tip("The best way to learn programming is by **building**. Every lesson in this app ends with something interactive or a small challenge — actually do them!"),
        ],
        quiz: [
            QuizQuestion(
                question: "Which language do we use to build apps for iPhone and Mac?",
                options: ["Swift", "HTML", "Python", "SwiftUI"],
                correctIndex: 0,
                explanation: "Swift is the language. SwiftUI is the UI framework you write *in* Swift."
            ),
            QuizQuestion(
                question: "SwiftUI is 'declarative'. That means…",
                options: [
                    "You describe what the UI should look like, and SwiftUI builds it",
                    "You position every pixel by hand",
                    "It only works on the Mac",
                    "It requires no code at all",
                ],
                correctIndex: 0,
                explanation: "You declare the desired result; the framework handles the drawing and updating."
            ),
        ]
    )

    static let variablesAndTypes = Lesson(
        id: "swift-02-variables-and-types",
        title: "Variables, Constants & Types",
        subtitle: "How programs remember things: let, var, and Swift's basic types.",
        minutes: 8,
        blocks: [
            .text("Programs work with **data**: names, scores, settings. Data lives in named containers, and in Swift you create them with two keywords:"),
            .code("""
            let name = "Ada"   // constant — can never change
            var score = 0      // variable — can change

            score = 10         // ✅ fine
            score += 5         // score is now 15
            // name = "Grace"  // ❌ error: 'name' is a constant
            """),
            .text("Every value has a **type**. The four you'll use constantly:"),
            .code("""
            let greeting: String = "Hello"  // text
            let lives: Int = 3              // whole numbers
            let price: Double = 9.99        // decimal numbers
            let isPremium: Bool = true      // true / false
            """),
            .text("Swift is smart: it **infers** the type, so `let lives = 3` already knows `lives` is an `Int`. But once set, a type never changes — Swift is **type-safe**, which catches whole categories of bugs before your app even runs."),
            .text("The most useful String trick is **interpolation** — embedding values inside text with `\\( )`:"),
            .code("""
            let player = "Ada"
            let points = 150
            let message = "Congrats \\(player), you scored \\(points) points!"
            // → "Congrats Ada, you scored 150 points!"
            """),
            .demo(.greeter),
            .tip("Prefer `let` unless you know the value must change. It makes your code safer and easier to reason about."),
        ],
        quiz: [
            QuizQuestion(
                question: "Which keyword creates a value that CAN change later?",
                options: ["var", "let", "func", "type"],
                correctIndex: 0,
                explanation: "`let` makes a constant; `var` makes a variable."
            ),
            QuizQuestion(
                question: "What is the type of `let pi = 3.14`?",
                options: ["Double", "Int", "String", "Bool"],
                correctIndex: 0,
                explanation: "Decimal literals infer as `Double`. `3` would be an `Int`."
            ),
            QuizQuestion(
                question: "How do you embed a value inside a string?",
                options: ["\\(value)", "+ value +", "%value%", "${value}"],
                correctIndex: 0,
                explanation: "Backslash-parentheses is Swift's string interpolation."
            ),
        ]
    )

    static let functionsAndOptionals = Lesson(
        id: "swift-03-functions-optionals",
        title: "Functions & Optionals",
        subtitle: "Reusable instructions, and Swift's superpower for handling missing data.",
        minutes: 8,
        blocks: [
            .text("A **function** packages instructions so you can reuse them. Functions can take **inputs** (parameters) and produce an **output** (a return value)."),
            .code("""
            func greet(name: String) -> String {
                return "Hello, \\(name)! 👋"
            }

            let message = greet(name: "Ada")   // "Hello, Ada! 👋"
            """),
            .text("Read the signature like a sentence: \"`greet` takes a `name` of type `String` and returns (`->`) a `String`.\""),
            .heading("Optionals: the billion-dollar fix"),
            .text("The most common crash in all of software is *missing data*. Swift tackles it with **optionals**. A normal `String` must always contain text. A `String?` (read: \"optional String\") may contain text — or `nil`, meaning *nothing*."),
            .code("""
            var nickname: String? = nil        // no nickname yet

            // Unwrap safely with 'if let'
            if let nickname {
                print("Hi, \\(nickname)")
            } else {
                print("No nickname set")
            }

            // Or provide a default value with ??
            let displayName = nickname ?? "Anonymous"
            """),
            .text("Swift *forces* you to deal with optionals before using them. That small bit of discipline is a big reason Swift apps crash less."),
            .tip("`if let` creates a temporary, guaranteed-non-nil copy you can use inside the braces. `??` is perfect for quick defaults."),
        ],
        quiz: [
            QuizQuestion(
                question: "What does `String?` mean?",
                options: [
                    "A string that may be missing (nil)",
                    "A question to the user",
                    "Two strings joined together",
                    "A compiler error",
                ],
                correctIndex: 0,
                explanation: "The question mark marks an optional: either a value or nil."
            ),
            QuizQuestion(
                question: "The safest way to use an optional's value is…",
                options: [
                    "Unwrap it with if let or guard let",
                    "Force unwrap it with !",
                    "Ignore the optional",
                    "Convert it to Int",
                ],
                correctIndex: 0,
                explanation: "Force unwrapping a nil optional crashes your app; if let never can."
            ),
        ]
    )

    // MARK: - Module 2: SwiftUI Essentials

    static let firstView = Lesson(
        id: "swiftui-01-first-view",
        title: "Your First View",
        subtitle: "Views, bodies, and modifiers — the atoms of every screen.",
        minutes: 8,
        blocks: [
            .text("In SwiftUI, **everything on screen is a `View`** — text, buttons, images, even entire screens. To make your own, you write a `struct` that conforms to the `View` protocol. Its single requirement: a property called `body`."),
            .code("""
            import SwiftUI

            struct ContentView: View {
                var body: some View {
                    Text("Hello, world! 🌍")
                }
            }
            """),
            .text("Read it aloud: \"`ContentView` is a `View` whose body contains *some view* — a `Text`.\" The `some View` return type means \"any kind of view, as long as it's always the same one.\""),
            .heading("Modifiers"),
            .text("You customize views with **modifiers** — methods that return a new, modified view. They read top-to-bottom, and **order matters**."),
            .code("""
            Text("SwiftUI is fun")
                .font(.largeTitle)          // make it big
                .bold()                     // make it bold
                .foregroundStyle(.purple)   // color the text
                .padding()                  // add space around it
                .background(.yellow, in: .capsule)
            """),
            .demo(.styledText),
            .tip("Mentally swap `.padding()` and `.background(...)`: padding-first means the background covers a larger area. Order. Matters."),
        ],
        quiz: [
            QuizQuestion(
                question: "Every screen or component in SwiftUI conforms to which protocol?",
                options: ["View", "Body", "Screen", "Widget"],
                correctIndex: 0,
                explanation: "The `View` protocol, with its required `body` property."
            ),
            QuizQuestion(
                question: "What does a modifier like `.bold()` do?",
                options: [
                    "Returns a new, modified view",
                    "Deletes the view",
                    "Compiles the app",
                    "Nothing until runtime",
                ],
                correctIndex: 0,
                explanation: "Modifiers wrap the view in a new view — that's why order matters."
            ),
        ]
    )

    static let stacks = Lesson(
        id: "swiftui-02-stacks",
        title: "Layout with Stacks",
        subtitle: "Arrange views vertically, horizontally, and in layers.",
        minutes: 8,
        blocks: [
            .text("You rarely place views at exact coordinates. Instead you **stack** them. SwiftUI has three stack types:"),
            .code("""
            VStack(spacing: 16) {   // vertical
                Text("Title")
                Text("Subtitle")
            }

            HStack {                // horizontal
                Image(systemName: "star.fill")
                Text("Favorite")
            }

            ZStack {                // layered, back to front
                Circle()
                Text("1")
            }
            """),
            .text("A `Spacer()` expands to push views apart, and `.padding()` adds breathing room. Real layouts are just **stacks inside stacks** — boxes within boxes. This row of a contact card is an `HStack` containing a `VStack`:"),
            .code("""
            HStack {
                Image(systemName: "person.circle.fill")
                VStack(alignment: .leading) {
                    Text("Ada Lovelace").bold()
                    Text("First programmer").foregroundStyle(.secondary)
                }
                Spacer()
                Image(systemName: "chevron.right")
            }
            .padding()
            """),
            .demo(.stackLayout),
            .tip("When a layout surprises you, sketch the stacks on paper. Every SwiftUI screen decomposes into H/V/Z stacks."),
        ],
        quiz: [
            QuizQuestion(
                question: "Which stack arranges views horizontally?",
                options: ["HStack", "VStack", "ZStack", "List"],
                correctIndex: 0,
                explanation: "H = horizontal, V = vertical, Z = layered depth."
            ),
            QuizQuestion(
                question: "What does `Spacer()` do?",
                options: [
                    "Expands to fill available space, pushing views apart",
                    "Adds exactly 8pt of padding",
                    "Deletes the previous view",
                    "Shows a space-themed icon",
                ],
                correctIndex: 0,
                explanation: "Spacer is a flexible, invisible view that greedily takes free space."
            ),
        ]
    )

    static let stateAndInteraction = Lesson(
        id: "swiftui-03-state",
        title: "State & Interaction",
        subtitle: "@State, buttons and bindings — make your UI react.",
        minutes: 10,
        blocks: [
            .text("So far our views are static. Real apps **react**: taps, typing, toggles. SwiftUI's core idea: *your UI is a function of your data*. Store changeable data in **`@State`**, and when it changes, SwiftUI **rebuilds the view automatically**."),
            .code("""
            struct CounterView: View {
                @State private var count = 0

                var body: some View {
                    VStack(spacing: 20) {
                        Text("Count: \\(count)")
                            .font(.largeTitle)
                        Button("Tap me!") {
                            count += 1   // the UI updates by itself 🎉
                        }
                    }
                }
            }
            """),
            .demo(.counter),
            .heading("Bindings: two-way connections"),
            .text("Controls like `TextField`, `Toggle` and `Slider` need to both *read* and *write* your state. You hand them a **binding** by writing `$` before the property name:"),
            .code("""
            @State private var name = ""
            @State private var isOn = true

            TextField("Your name", text: $name)   // $ = read AND write
            Toggle("Notifications", isOn: $isOn)
            """),
            .demo(.colorMixer),
            .tip("Golden rule: the view owns `@State`. When data must be *shared* between views, you pass a `@Binding` down to the child view."),
        ],
        quiz: [
            QuizQuestion(
                question: "Which property wrapper lets a view own simple, changeable data?",
                options: ["@State", "@Environment", "@MainActor", "@Sendable"],
                correctIndex: 0,
                explanation: "@State stores value-type data owned by the view; changes refresh the UI."
            ),
            QuizQuestion(
                question: "What does `$name` create?",
                options: [
                    "A Binding — a two-way connection to the state",
                    "A copy of the string",
                    "A constant",
                    "A new view",
                ],
                correctIndex: 0,
                explanation: "The $ prefix reads the binding from the @State property wrapper."
            ),
        ]
    )

    static let listsAndNavigation = Lesson(
        id: "swiftui-04-lists-navigation",
        title: "Lists & Navigation",
        subtitle: "Lists of data, and tapping through to detail screens.",
        minutes: 10,
        blocks: [
            .text("Almost every app follows the same pattern: **a list of things you tap to see details**. `List` + `NavigationStack` + `NavigationLink` give you that pattern nearly for free."),
            .text("To show your own data in a list, make it **`Identifiable`** — give each item a unique `id` so SwiftUI can track rows as they change:"),
            .code("""
            struct Language: Identifiable {
                let id = UUID()     // unique every time
                let name: String
                let emoji: String
            }

            let languages = [
                Language(name: "Swift", emoji: "🐦"),
                Language(name: "Rust", emoji: "🦀"),
                Language(name: "Python", emoji: "🐍"),
            ]
            """),
            .code("""
            NavigationStack {
                List(languages) { language in
                    NavigationLink {
                        Text("You picked \\(language.name)!")   // detail view
                    } label: {
                        Text("\\(language.emoji) \\(language.name)")
                    }
                }
                .navigationTitle("Languages")
            }
            """),
            .demo(.listNavigation),
            .tip("Use `ForEach` to render any collection anywhere; `List` adds the platform look: rows, separators, swipe actions."),
        ],
        quiz: [
            QuizQuestion(
                question: "Why must list data be `Identifiable`?",
                options: [
                    "So SwiftUI can tell items apart when updating",
                    "It's required by App Store law",
                    "For encryption",
                    "So they sort alphabetically",
                ],
                correctIndex: 0,
                explanation: "Stable identities let SwiftUI animate insertions, deletions and moves correctly."
            ),
            QuizQuestion(
                question: "Which container enables push-style navigation?",
                options: ["NavigationStack", "VStack", "ZStack", "Form"],
                correctIndex: 0,
                explanation: "NavigationStack manages a stack of pushed views; NavigationLink pushes onto it."
            ),
        ]
    )

    // MARK: - Module 3: Build Real Things

    static let dataAndModels = Lesson(
        id: "build-01-models",
        title: "Modeling Your Data",
        subtitle: "Structs and value types — the heart of every app.",
        minutes: 8,
        blocks: [
            .text("Real apps revolve around **models**: plain structs describing your data. A to-do app has `Task`s; a chat app has `Message`s; a weather app has `Forecast`s."),
            .code("""
            struct Task: Identifiable {
                let id = UUID()
                var title: String
                var isDone = false
            }
            """),
            .text("Why a `struct`? Structs are **value types**: copies are fully independent, and SwiftUI is built around that — when a value changes, the UI knows it must refresh."),
            .heading("One source of truth"),
            .text("Keep your app's data in **one** `@State` property — the *single source of truth* — and change it through small, clearly named methods:"),
            .code("""
            @State private var tasks = [
                Task(title: "Learn Swift"),
                Task(title: "Build an app"),
            ]

            func toggle(_ task: Task) {
                guard let i = tasks.firstIndex(where: { $0.id == task.id }) else { return }
                tasks[i].isDone.toggle()
            }
            """),
            .text("The `{ $0.id == task.id }` part is a **closure** — a mini function passed as an argument. `$0` is its first parameter. You'll see closures everywhere in Swift."),
            .tip("Design the model first, UI second. If your data is well shaped, the interface almost writes itself."),
        ],
        quiz: [
            QuizQuestion(
                question: "In SwiftUI apps, data models are usually…",
                options: ["structs", "classes", "enums", "protocols"],
                correctIndex: 0,
                explanation: "Value-type structs are the default; SwiftUI's update model is built on them."
            ),
            QuizQuestion(
                question: "What is a 'single source of truth'?",
                options: [
                    "One place that owns the data; all views read from it",
                    "A fancy database",
                    "The App Store",
                    "A secret API key",
                ],
                correctIndex: 0,
                explanation: "One owner means no conflicting copies — the UI always shows the real state."
            ),
        ]
    )

    static let capstoneTodo = Lesson(
        id: "build-02-capstone-todo",
        title: "Capstone: A Working To-Do App",
        subtitle: "Combine everything into a real, working app.",
        minutes: 12,
        blocks: [
            .text("Time to combine **everything**: models, state, lists, bindings, stacks. Here is a complete to-do app — read it top to bottom and you'll recognize every single piece:"),
            .code("""
            struct Task: Identifiable {
                let id = UUID()
                var title: String
                var isDone = false
            }

            struct TodoView: View {
                @State private var tasks: [Task] = []
                @State private var newTitle = ""

                var body: some View {
                    NavigationStack {
                        VStack {
                            HStack {
                                TextField("New task…", text: $newTitle)
                                Button("Add") { addTask() }
                                    .disabled(newTitle.isEmpty)
                            }
                            .padding()

                            List {
                                ForEach(tasks) { task in
                                    HStack {
                                        Image(systemName: task.isDone
                                              ? "checkmark.circle.fill" : "circle")
                                            .onTapGesture { toggle(task) }
                                        Text(task.title)
                                            .strikethrough(task.isDone)
                                    }
                                }
                                .onDelete { tasks.remove(atOffsets: $0) }
                            }
                        }
                        .navigationTitle("My Tasks")
                    }
                }

                func addTask() {
                    tasks.append(Task(title: newTitle))
                    newTitle = ""
                }

                func toggle(_ task: Task) {
                    guard let i = tasks.firstIndex(where: { $0.id == task.id })
                    else { return }
                    tasks[i].isDone.toggle()
                }
            }
            """),
            .demo(.todoList),
            .text("Notice the structure: **model → state → view → actions**. You'll reuse this same skeleton for almost every app you ever build."),
            .challenge("Make it yours: 1) Show \"X of Y done\" in the title. 2) Add an emoji picker per task. 3) Add a Toggle that hides completed tasks. Small steps = real learning."),
        ],
        quiz: [
            QuizQuestion(
                question: "Where does the `tasks` array live?",
                options: [
                    "In an @State property on the view",
                    "Inside each row",
                    "On the App Store",
                    "Inside a Text view",
                ],
                correctIndex: 0,
                explanation: "The view owns the array as its single source of truth."
            ),
            QuizQuestion(
                question: "Why is the Add button `.disabled(newTitle.isEmpty)`?",
                options: [
                    "To prevent empty tasks — the UI reacting to state",
                    "It's a bug",
                    "Purely decorative",
                    "Swift requires it",
                ],
                correctIndex: 0,
                explanation: "A declarative UI rule: whenever newTitle is empty, the button disables itself."
            ),
        ]
    )

    static let nextSteps = Lesson(
        id: "build-03-next-steps",
        title: "Next Steps & How This App Was Built",
        subtitle: "Read this app's source, install Xcode, and keep building.",
        minutes: 6,
        blocks: [
            .text("🎓 You've covered the core of app development: **Swift basics, views, layout, state, lists, navigation and models**. Where next?"),
            .heading("Learn from this very app"),
            .text("This learning app is itself a SwiftUI app — and its source code is your next textbook. Open the project folder and read the files in this order:"),
            .code("""
            Sources/SwiftSchool/
            ├── SwiftSchoolApp.swift    // 1️⃣ the @main entry point
            ├── Models/Lesson.swift     // 2️⃣ data models (like your Task)
            ├── Data/Curriculum.swift   // 3️⃣ the content you're reading!
            ├── Views/ContentView.swift // 4️⃣ NavigationSplitView layout
            ├── Views/LessonViews.swift // 5️⃣ rendering lesson blocks
            └── Views/Demos.swift       // 6️⃣ every demo you played with
            """),
            .heading("Build for iPhone"),
            .text("Everything you learned works **identically on iOS**. Download **Xcode** (free on the Mac App Store), create a project with *iOS → App*, and run it on the iPhone **Simulator** — or on your real iPhone."),
            .text("Excellent free resources: Apple's official *SwiftUI Tutorials* (developer.apple.com), *Hacking with Swift* (hackingwithswift.com), and *Swift Playgrounds* on iPad and Mac."),
            .tip("The real secret: build lots of tiny apps. A dice roller. A tip calculator. A habit tracker. Finishing small things beats starting big things."),
            .challenge("Homework: build the dice roller 🎲 — one `@State` Int, one `Button`, one big `Text`. You already know everything you need."),
        ],
        quiz: [
            QuizQuestion(
                question: "Which tool do you install to run apps on the iPhone Simulator?",
                options: ["Xcode", "Safari", "Terminal only", "App Store Connect"],
                correctIndex: 0,
                explanation: "Xcode is Apple's free development environment, including simulators."
            ),
            QuizQuestion(
                question: "The most effective way to keep learning is…",
                options: [
                    "Build many small, finishable apps",
                    "Read one giant book cover to cover",
                    "Wait until you feel ready",
                    "Memorize the documentation",
                ],
                correctIndex: 0,
                explanation: "Small finished projects compound into real skill."
            ),
        ]
    )
}
