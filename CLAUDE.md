# CLAUDE.md — OS Repo Project Instructions

> OS-level instructions (session protocol, beads workflow, model routing tiers, escalation policy, blog pipeline, base rules) are inherited from `~/.claude/CLAUDE.md`. This file contains only OS-repo-specific configuration.

## Project

**OS**: The project operating system — shared tooling, user-level Claude instructions, and project template. This is the first thing cloned on a new machine. Everything here is project-agnostic; if it's specific to one project, it belongs in that project's repo instead.

## Philosophy: Machines Are Cattle

Machines — servers, workstations, laptops — are disposable. This repo is the single entry point that takes a bare machine to a fully operational environment. Clone it, run `setup.sh`, and everything needed to work on existing projects or spin up new ones is in place. No snowflake configurations, no "works on my machine" state. If a machine dies, a new one gets the same treatment. The OS repo is the only thing that needs to survive.

## What This Repo Contains

| Directory | Purpose | Consumers |
|-----------|---------|-----------|
| `claude/CLAUDE.md` | User-level instructions (symlinked → `~/.claude/CLAUDE.md`) | Every Claude Code session on this machine |
| `docker/` | Shared Dockerfiles + compose for `bd` and `gh` | Every project (via PATH wrappers) |
| `bin/` | Self-resolving wrappers: `bd`, `gh` (symlinked → `~/.local/bin/`) | Every project |
| `template/` | Project skeleton: CLAUDE.md, BOOTSTRAP.md, agent specs, blog dirs | `new-project.sh` copies this |
| `docs/` | OS-level protocols and reference docs | Claude sessions in this repo |
| `setup.sh` | One-time machine bootstrap (symlinks bins + CLAUDE.md) | New machine setup |
| `new-project.sh` | Scaffold new project from template | User starting a new project |

## Project Spin-Up

When a user describes a new project in this repo's context, follow the **spin-up protocol** in `docs/spin-up-protocol.md`. This handles conversational intake (project name, agents, model mapping) and mechanical execution (scaffolding, CLAUDE.md pre-fill, GitHub repo creation, beads init) — then hands the user off to the new project directory to finish bootstrap.

**Trigger:** User describes a project they want to create, or asks to spin up / start / create a new project.

## Agent Roster

This repo is small and meta — it doesn't need a full agent team.

| Agent | Role |
|-------|------|
| PM | Maintain the OS: update shared instructions, improve template, keep tooling working |

**No routing rules needed** — all work is PM-scope.

## Task-Type → Model Mapping

| Task Type | Model | Rationale |
|-----------|-------|-----------|
| Evolve OS patterns (new workflow, new rule) | **Opus** | Cross-project pattern synthesis |
| Update shared instructions or template | **Sonnet** | Structured editing with consistency checks |
| Fix wrapper scripts or Dockerfiles | **Haiku** | Mechanical: shell scripts, Docker config |

## Token Optimization

**Standing order: minimize token utilization.** See `~/.claude/CLAUDE.md` for the full policy. Key points:
- Default to Haiku for mechanical work
- Use tools and `--json` parsing over LLM interpretation
- Concise subagent prompts with file refs, not pasted content
- One focused task per agent dispatch
- No verbose outputs — write the deliverable, not a summary of it

## Design Change Cascade

Changes to the OS repo affect every project on the machine. The cascade is simpler than a product project but still mandatory.

A "design change" is any modification to:
- `claude/CLAUDE.md` (affects all project sessions)
- `docker/` (affects shared tooling images)
- `bin/` (affects shared CLI wrappers)
- `template/` (affects future projects, NOT existing ones)

```
OS Change (parent)
├── 1. Compatibility Check (P1, blocked by parent)
│      Does this break existing projects?
│      Check: can bd/gh still run from an existing project directory?
│      Check: does the CLAUDE.md change contradict any project-level CLAUDE.md?
│      Output: go/no-go
│
└── 2. Template Sync (P2, blocked by Compatibility Check)
       Does the template need updating to match?
       If claude/CLAUDE.md changed: does template/CLAUDE.md still make sense?
       If docker/ changed: does template/docker-compose.yml comment still accurate?
       Output: template update or "no template impact"
```

### Template Changes Are Forward-Only

Changes to `template/` only affect future projects created with `new-project.sh`. Existing projects are NOT automatically updated. If an OS change is valuable enough to backport, create a bead in each affected project's repo.

## Source of Truth Hierarchy

1. **This repo** — the OS patterns, shared instructions, and template are the source of truth for how projects operate
2. **Project-level CLAUDE.md** — projects can override or extend OS instructions; project-specific config always wins in that project's context
3. **Beads in this repo** — track OS evolution decisions

## Artifact Conventions

- **Shell scripts**: POSIX-compatible bash in `bin/` and repo root. Executable bit set. Use `readlink -f` for self-resolution.
- **Dockerfiles**: Minimal images in `docker/`. Named `Dockerfile.<service>`.
- **Instructions**: Markdown. `claude/CLAUDE.md` is the main artifact.
- **Template files**: In `template/`. Placeholders use `[BRACKETS]`.

## Repo Structure

```
os/
├── CLAUDE.md              # This file — OS repo project instructions
├── VERSION                # OS version number (integer, increments on notable changes)
├── CHANGELOG.md           # What changed in each version + backport guidance
├── setup.sh               # Machine bootstrap (symlinks)
├── new-project.sh         # Scaffold new project from template
├── claude/
│   └── CLAUDE.md          # User-level instructions (symlinked → ~/.claude/)
├── docker/
│   ├── Dockerfile.beads   # Alpine + beads CLI
│   ├── Dockerfile.gh      # Alpine + GitHub CLI
│   └── docker-compose.yml # Shared services (PROJECT_ROOT-aware)
├── bin/
│   ├── bd                 # Beads wrapper (symlinked → ~/.local/bin/)
│   ├── gh                 # GitHub CLI wrapper (symlinked → ~/.local/bin/)
│   ├── os                 # OS management CLI: bootstrap, status, projects
│   └── os-check           # Version compliance checker (symlinked → ~/.local/bin/)
├── docs/
│   ├── spin-up-protocol.md # Conversational project creation protocol
│   └── bootstrap-config.md # os.yml format spec + bootstrap architecture
├── template/              # Project skeleton (copied by new-project.sh)
│   ├── CLAUDE.md          # Project instructions template
│   ├── BOOTSTRAP.md       # 9-section setup checklist (spin-up aware)
│   ├── docker-compose.yml # Project-specific services placeholder
│   ├── .gitignore
│   └── docs/
│       ├── agent-TEMPLATE.md
│       ├── agent-blog.md   # Blog agent (voice profile carries across projects)
│       ├── product-vision.md
│       └── blog/
│           ├── candidates.md
│           ├── drafts/
│           └── posts/
└── .beads/                # Beads database (git-tracked)
```

## Project-Specific Rules

1. **Project-agnostic only**: Nothing in this repo should reference a specific project. If you're writing something that only applies to Aerocloak (or any other project), it belongs in that project's repo.
2. **Backward compatibility**: Changes to `claude/CLAUDE.md`, `docker/`, or `bin/` must not break existing projects. Always run the compatibility check.
3. **Template is forward-only**: Don't try to auto-update existing projects when the template changes. Create project-specific beads if backporting is needed.
4. **Test wrappers after changes**: After modifying `bin/` or `docker/`, verify `bd --version` and `gh --version` work from an existing project directory.
