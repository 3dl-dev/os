#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Installing OS tools..."

# Symlink wrappers to ~/.local/bin (assumed on PATH)
mkdir -p "$HOME/.local/bin"
ln -sf "$SCRIPT_DIR/bin/bd" "$HOME/.local/bin/bd"
ln -sf "$SCRIPT_DIR/bin/gh" "$HOME/.local/bin/gh"
ln -sf "$SCRIPT_DIR/new-project.sh" "$HOME/.local/bin/new-project"

# Symlink user-level Claude instructions
mkdir -p "$HOME/.claude"
if [ -f "$HOME/.claude/CLAUDE.md" ] && [ ! -L "$HOME/.claude/CLAUDE.md" ]; then
  echo "WARNING: ~/.claude/CLAUDE.md exists and is not a symlink."
  echo "  Back it up and re-run, or manually symlink:"
  echo "  ln -sf $SCRIPT_DIR/claude/CLAUDE.md ~/.claude/CLAUDE.md"
else
  ln -sf "$SCRIPT_DIR/claude/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
  echo "  Linked ~/.claude/CLAUDE.md"
fi

# Pre-build shared Docker images
echo "Building shared Docker images..."
docker compose -f "$SCRIPT_DIR/docker/docker-compose.yml" build

echo ""
echo "Done. Verify:"
echo "  bd --version"
echo "  gh --version"
echo ""
echo "Create a new project:"
echo "  new-project ~/projects/my-thing"
