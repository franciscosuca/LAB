# SwiftSchool 🎓

A macOS desktop app that **teaches you how to program apps** — and whose own
source code is your next textbook. Built with Swift + SwiftUI, the same tools
used for iPhone apps.

![Platform](https://img.shields.io/badge/platform-macOS%2013%2B-blue)
![Language](https://img.shields.io/badge/language-Swift%205.9-orange)

## What's inside

- **10 guided lessons** across 3 modules:
  1. *Swift Foundations* — how apps work, variables & types, functions & optionals
  2. *SwiftUI Essentials* — views & modifiers, stacks, state, lists & navigation
  3. *Build Real Things* — data models, a full to-do app capstone, next steps
- **7 interactive live demos** — real SwiftUI running inside the lessons, with
  code that updates as you play
- **Quizzes** with instant feedback and explanations
- **Progress tracking**, saved between launches

## Requirements

- macOS 13 or later
- A Swift toolchain — either **Xcode** or the **Command Line Tools**
  (`xcode-select --install`). No Xcode required to run *this* app.

## Run it

```bash
cd ios-test
./run.sh
```

The first build takes a minute. A window titled **SwiftSchool** will appear —
if it opens behind other windows, look for it in the Dock. Quit with `⌘Q` or
by closing the window.

> **Why a script instead of `swift build`?** The Command Line Tools install on
> this machine has a broken Swift Package Manager (its PackageDescription
> library is missing symbols). `run.sh` simply compiles the sources with
> `swiftc` directly — same result. Once you install full Xcode, this folder
> also works as a normal SwiftPM package: open `Package.swift` in Xcode and
> press **⌘R**.

## Learn from this app's own code

The app is deliberately small and readable. Read the source in this order —
it's the curriculum's final lesson:

```
Sources/SwiftSchool/
├── SwiftSchoolApp.swift        // 1️⃣ the @main entry point
├── Models/Lesson.swift         // 2️⃣ data models (structs, enums)
├── Models/ProgressStore.swift  // 3️⃣ ObservableObject + UserDefaults
├── Data/Curriculum.swift       // 4️⃣ all lesson content, as data
├── Utilities/SyntaxHighlighter.swift  // 5️⃣ regex → AttributedString
├── Views/ContentView.swift     // 6️⃣ NavigationSplitView layout
├── Views/LessonViews.swift     // 7️⃣ rendering lesson blocks
├── Views/CodeBlockView.swift   // 8️⃣ code display + copy to clipboard
├── Views/QuizView.swift        // 9️⃣ interactive quizzes
└── Views/Demos.swift           // 🔟 every live demo you played with
```

## Next step: iPhone

Everything in this project (SwiftUI views, `@State`, `NavigationStack`, …)
works identically on iOS. Install **Xcode** from the Mac App Store, then:

- Open this folder in Xcode (`Package.swift` is a valid Xcode project), or
- Create a new project with *iOS → App* and start building for iPhone.

Great free resources: Apple's *SwiftUI Tutorials* (developer.apple.com),
*Hacking with Swift* (hackingwithswift.com), and *Swift Playgrounds*.
