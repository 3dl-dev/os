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

cd "$TARGET"
git init
git add -A
git commit -m "Bootstrap project from OS template"

echo ""
echo "Project created at $TARGET"
echo ""
echo "Next steps:"
echo "  cd $TARGET"
echo "  bd init                    # Initialize beads"
echo "  vi BOOTSTRAP.md            # Walk through the setup checklist"
echo "  vi CLAUDE.md               # Fill in project-specific sections"
