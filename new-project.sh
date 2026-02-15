#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: new-project <directory> [--org <org-name>]"
  echo "  Creates a new project from the OS template."
  echo "  --org: Register the project in the specified org's os.yml"
  exit 1
fi

REAL_SCRIPT="$(readlink -f "${BASH_SOURCE[0]}")"
SCRIPT_DIR="$(cd "$(dirname "$REAL_SCRIPT")" && pwd)"
TARGET="$1"
ORG_NAME=""

# Parse --org flag
shift
while [ $# -gt 0 ]; do
  case "$1" in
    --org) ORG_NAME="$2"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

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

# Auto-detect org if not specified
OS_CONF="$HOME/.local/share/os/os.conf"
if [ -z "$ORG_NAME" ] && [ -f "$OS_CONF" ]; then
  # Use first org in os.conf (most setups have one org)
  ORG_NAME=$(head -n 2 "$OS_CONF" | grep -v '^#' | head -1 | awk '{print $1}')
fi

# Register in org's os.yml if org is known
if [ -n "$ORG_NAME" ] && [ -f "$OS_CONF" ]; then
  ORG_PATH=$(grep "^$ORG_NAME " "$OS_CONF" | awk '{print $2}')
  OS_YML="$ORG_PATH/os.yml"

  if [ -f "$OS_YML" ]; then
    PROJECT_NAME=$(basename "$TARGET")
    FULL_TARGET=$(cd "$TARGET" 2>/dev/null && pwd || readlink -f "$TARGET")

    # Check if project already registered
    if grep -q "^  $PROJECT_NAME:" "$OS_YML" 2>/dev/null; then
      echo "  Project '$PROJECT_NAME' already in $OS_YML"
    else
      # Append project to os.yml projects section
      # Use ~ path if it's under home
      DISPLAY_PATH="$FULL_TARGET"
      if [[ "$FULL_TARGET" == "$HOME"* ]]; then
        DISPLAY_PATH="~${FULL_TARGET#$HOME}"
      fi

      # Add to projects section (before dashboard section or at end)
      if grep -q "^dashboard:" "$OS_YML"; then
        sed -i "/^dashboard:/i\\  $PROJECT_NAME:\n    path: $DISPLAY_PATH\n    bead-prefix: $PROJECT_NAME" "$OS_YML"
      else
        echo "  $PROJECT_NAME:" >> "$OS_YML"
        echo "    path: $DISPLAY_PATH" >> "$OS_YML"
        echo "    bead-prefix: $PROJECT_NAME" >> "$OS_YML"
      fi
      echo "  Registered in $OS_YML"

      # Re-run bootstrap to regenerate derived configs
      if [ -x "$SCRIPT_DIR/bin/os" ]; then
        "$SCRIPT_DIR/bin/os" bootstrap "$ORG_PATH" > /dev/null 2>&1 && \
          echo "  Dashboard config regenerated"
      fi
    fi
  fi
fi

echo ""
echo "Next steps:"
echo "  cd $TARGET"
echo "  claude                     # Start a session — Claude will walk you through bootstrap"
