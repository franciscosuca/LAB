import SwiftUI

/// A tiny regex-based Swift syntax highlighter.
/// It walks the code once, coloring comments, strings, keywords,
/// @attributes, numbers and TypeNames — a simplified Xcode palette.
enum SyntaxHighlighter {

    static func highlight(_ code: String) -> AttributedString {
        // Alternation order matters: comments and strings win over keywords.
        let pattern = #"(//[^\n]*)"#            // 1: comments
            + ##"|("(?:\\.|[^"\\])*")"##        // 2: string literals
            + #"|\b(import|struct|class|enum|protocol|extension|func|let|var|return|if|else|guard|switch|case|default|for|while|repeat|in|where|do|try|catch|throw|throws|async|await|some|any|nil|true|false|self|Self|super|init|deinit|static|private|public|internal|fileprivate|open|final|override|mutating|nonmutating|lazy|weak|unowned|typealias|break|continue|fallthrough|defer|is|as|inout)\b"#
            + #"|(@[A-Za-z]+)"#                  // 4: @attributes like @State
            + #"|\b(\d+(?:\.\d+)?)\b"#          // 5: numbers
            + #"|\b([A-Z][A-Za-z0-9_]*)\b"#     // 6: TypeNames

        guard let regex = try? NSRegularExpression(pattern: pattern) else {
            return AttributedString(code)
        }

        let nsRange = NSRange(code.startIndex..<code.endIndex, in: code)
        var result = AttributedString()
        var cursor = code.startIndex

        regex.enumerateMatches(in: code, range: nsRange) { match, _, _ in
            guard let match, let range = Range(match.range, in: code) else { return }

            // Plain text between the previous token and this one.
            if cursor < range.lowerBound {
                result += AttributedString(String(code[cursor..<range.lowerBound]))
            }

            var token = AttributedString(String(code[range]))
            token.foregroundColor = color(for: match)
            result += token
            cursor = range.upperBound
        }

        if cursor < code.endIndex {
            result += AttributedString(String(code[cursor...]))
        }
        return result
    }

    /// Which capture group matched decides the color.
    private static func color(for match: NSTextCheckingResult) -> Color {
        for group in 1...6 where match.range(at: group).location != NSNotFound {
            switch group {
            case 1: return .green   // comments
            case 2: return .red     // strings
            case 3: return .purple  // keywords
            case 4: return .orange  // @attributes
            case 5: return .blue    // numbers
            default: return .teal   // types
            }
        }
        return .primary
    }
}
