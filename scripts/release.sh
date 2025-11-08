#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
VERSION_FILE="$ROOT/version.txt"
TEST_CMD="pytest -q"
BUILD_SCRIPT="$ROOT/scripts/build.sh"
DIST_DIR="$ROOT/dist"

if [[ ! -f "$VERSION_FILE" ]]; then
echo "0.1.0" > "$VERSION_FILE"
fi
VERSION="$(cat "$VERSION_FILE")"

echo "Running tests..."
if command -v pytest >/dev/null 2>&1; then
  $TEST_CMD || { echo "Tests failed" >&2; exit 2; }
else
  echo "pytest not installed; skipping tests" >&2
fi

echo "Building extension packages..."
"$BUILD_SCRIPT"

echo "Creating git tag v$VERSION..."
if git rev-parse --git-dir >/dev/null 2>&1; then
  if git rev-parse "v$VERSION" >/dev/null 2>&1; then
    echo "Tag v$VERSION already exists" >&2
  else
    git add dist/*.zip || true
    git commit -m "Build artifacts for v$VERSION" || true
    git tag -a "v$VERSION" -m "Release v$VERSION"
    echo "Created tag v$VERSION"
  fi
else
  echo "Git not initialized; skipping tag" >&2
fi

echo "To push release:"
echo "  git push origin main --tags"

echo "Release script complete."