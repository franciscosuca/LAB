#!/bin/bash
# Build & launch SwiftSchool.
#
# This uses `swiftc` directly instead of `swift build`, because the
# Command Line Tools install on this machine has a broken SwiftPM
# (PackageDescription link failure). With full Xcode, both work.
set -e
cd "$(dirname "$0")"

echo "🔨 Building SwiftSchool…"
mkdir -p .build
# Compile every .swift file in Sources/SwiftSchool into one executable.
# Add -O for an optimized (slower to build) binary.
swiftc -o .build/SwiftSchool $(find Sources/SwiftSchool -name '*.swift')

echo "🚀 Launching…"
open -na "$PWD/.build/SwiftSchool"
