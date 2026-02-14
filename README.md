# OS — Project Operating System

The single entry point for getting a machine to spec. Clone this, run setup, and you're ready to work on any existing project or spin up new ones.

Machines are cattle. If one dies, clone this repo on the replacement and pick up where you left off.

## Prerequisites

You need three things installed on the bare machine:

1. **Git** — to clone this repo and your projects
2. **Docker** (with Compose) — all tooling runs in containers, nothing gets installed on the host
3. **Claude Code** — `npm install -g @anthropic-ai/claude-code` (or however you last installed it)

Everything else — beads, GitHub CLI, project-specific tooling — runs in Docker.

## Fresh Machine Setup

```bash
git clone <this-repo> ~/projects/os
cd ~/projects/os
./setup.sh
```

`setup.sh` does three things:
- Symlinks `bd`, `gh`, and `new-project` to `~/.local/bin/` (must be on PATH)
- Symlinks `claude/CLAUDE.md` to `~/.claude/CLAUDE.md` (Claude Code picks this up automatically)
- Builds the shared Docker images (beads CLI, GitHub CLI)

Verify it worked:

```bash
bd --version
gh --version
```

## Working on an Existing Project

```bash
cd ~/projects/<project-name>
claude
```

Claude reads the project's `CLAUDE.md`, runs `bd ready`, and picks up where you left off.

## Creating a New Project

### Conversational (recommended)

```bash
cd ~/projects/os
claude
```

Describe the project you want to create. Claude handles everything — scaffolding the directory, pre-filling CLAUDE.md with your project identity, agents, and model mapping, creating the GitHub repo, and initializing beads. When it's done, it tells you to:

```bash
cd ~/projects/<project-name> && claude
```

The new project session picks up where spin-up left off, walking you through the remaining setup (container services, design cascade, artifact conventions, etc.).

### Manual (alternative)

```bash
new-project ~/projects/<project-name>
cd ~/projects/<project-name>
claude
```

Claude detects the unbootstrapped project and walks you through the full interactive setup from scratch.

## What's in the Box

| Directory | What it does |
|-----------|-------------|
| `claude/CLAUDE.md` | User-level instructions that apply to every Claude session on this machine |
| `docker/` | Shared Dockerfiles and compose config for `bd` (beads) and `gh` (GitHub CLI) |
| `bin/` | Thin shell wrappers that resolve back to the Docker services |
| `template/` | Project skeleton — copied by `new-project`, bootstrapped interactively by Claude |
| `setup.sh` | One-time machine setup |
| `new-project.sh` | Scaffold a new project from the template |

## Updating the OS

Pull changes and re-run setup to pick up new tooling or instruction updates:

```bash
cd ~/projects/os
git pull
./setup.sh
```

Existing projects are not automatically updated when the template changes. If an OS change is worth backporting to a project, do it in that project's repo.
