#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: new-project <directory>"
  echo "  Creates a new project from the OS template."
  exit 1
fi

REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
TARGET="$1"

if [ -d "$TARGET" ]; then
  echo "Error: $TARGET already exists"
  exit 1
fi

cp -r "$SCRIPT_DIR/template" "$TARGET"

# Stamp OS version into the new project
OS_VERSION=$(cat "$SCRIPT_DIR/VERSION")
echo "$OS_VERSION" > "$TARGET/.os-version"

cd "$TARGET"
git init
git add -A
git commit -m "Bootstrap project from OS template"

echo ""
echo "Project created at $TARGET"
echo ""
echo "Next steps:"
echo "  cd $TARGET"
echo "  claude                     # Start a session — Claude will walk you through bootstrap"
