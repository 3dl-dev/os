# CLAUDE.md — OS Repo Project Instructions

> OS-level instructions (session protocol, beads workflow, model routing tiers, escalation policy, blog pipeline, base rules) are inherited from `~/.claude/CLAUDE.md`. This file contains only OS-repo-specific configuration.

## Project

**OS**: The AI Enterprise OS — a three-layer platform where AI agents manage organizational workflows through three surfaces (Console, Web, Teams). The OS provides domain-agnostic infrastructure: state management (bd/beads), REST API, web dashboard, Teams bot, agent invocation, and Docker conventions. Organizations configure it; projects consume it.

Architecture: `docs/architecture.md` (the founding design doc — read it, don't rewrite it).

## The Mission

The OS exists to **self-host an AI executive team**. The founder defines specs and answers questions. The AI team does the thinking, research, analysis, drafting, and coordination. The OS is the platform that makes this work.

**Three surfaces, one state:**
- **Console** (CLI/Claude Code) — deep work, system changes, architecture. Flynn's grid.
- **Web** (dashboard.3dl.dev) — deliverable review, staff actions. The founder sees what the AI team produced and acts on it.
- **Teams** (bot) — conversational ops, real-time. "What's ready?" from your phone.

All three surfaces read/write the same beads state through the API. The founder uses whichever surface fits the moment.

**The staff queue is the gravity well.** The AI team works autonomously — researching, drafting, analyzing, coordinating across projects. When work reaches the point where a human must act (sign a contract, make a phone call, approve a strategy, review a deliverable), it lands in the staff queue. The three surfaces show the staff queue. The founder processes it. The AI team picks up from there.

**Agent Invocation is the core.** Without it, the OS is a fancy todo list. With it, the OS is a self-hosting AI management platform. The system spawns Claude agents with the right agent spec as system prompt, the right model tier for the task, and the right bead context. The agent does work, writes results to beads, and the three surfaces show what happened. This is the piece that makes it all real.

**This is the control plane.** The OS is the management interface for ALL projects in the portfolio (3DL ops, Aerocloak, GalTrader, etc.). It's how the founder sees what the AI team is doing across every project, acts on what needs human attention, and lets the AI team pick up from there. Right now the projects are managed through ad-hoc Claude Code sessions. The OS replaces that with a unified interface — three surfaces showing the same state, agents invoked through the platform instead of manually, staff queue items surfaced automatically.

**3DL is the reference implementation.** The org layer (`~/projects/3dl/`) defines agents (CEO, CFO, Strategist, Counsel, CPEO, CIO, Marketing), authority tiers, and workflows. The OS layer provides the machinery. Get it working for 3DL first — one org, one founder, real projects.

## CURRENT PHASE: Deploy and Ship (2026-02-15)

**The architecture doc is DONE. The API and bot code are WRITTEN. Nothing is RUNNING.**

Your job is to get this system live, not design more of it. Run `bd ready --no-daemon` for your work queue. Follow the dependency chain starting from the first unblocked P0 task.

### What Went Wrong (Context for Why These Rules Exist)

A previous session wrote an excellent architecture doc and built real API + bot code, then **veered sideways into framework-building**: a 722-line multi-org bootstrap CLI, a version alignment system, signal protocol tooling. These are premature abstractions — there is ONE org, ONE user, ONE machine. The session ended with "all beads closed" but nothing deployed. Code that doesn't run isn't shipped.

The pattern: after finishing the two MVPs (API + bot), the session went **sideways into infrastructure** instead of **upward on the critical path** toward Agent Invocation and deployment. It built governance frameworks for a system that doesn't exist yet.

### Hard Rules for This Phase

1. **DO NOT write design docs, protocol specs, or framework features.** The architecture doc is complete. The signal protocol spec exists. The bootstrap CLI exists. Stop designing, start deploying.
2. **DO NOT extend bin/os, os-check, or the version alignment system.** These are frozen (os-57b, os-pqb, os-snn). They were premature abstractions for multi-org/multi-install scenarios that don't exist.
3. **DO NOT build for hypothetical scale.** There is ONE org (3DL), ONE user, ONE machine. Build for that. Multi-org, multi-tenant, version compliance — all irrelevant until the single-org case works end-to-end.
4. **Ship means RUNNING, not "code exists."** A task is done when the thing serves real requests, not when unit tests pass with mocks. If docker-compose up doesn't work, the code isn't done.
5. **Fix what breaks on first real run.** The existing code was tested with mocks. Real execution will surface real bugs. Fixing them IS the high-value work.
6. **The finish line is os-844:** trigger agent work from a surface (Teams or Web), see the result appear in all three surfaces. When that works, the OS self-hosts its AI team.

### What Exists (Inventory)

| Component | Code | Status |
|-----------|------|--------|
| API server (`api/main.py`) | FastAPI, 8 endpoints wrapping bd | Written, never run for real |
| Teams bot (`bot/`) | Bot Framework, Adaptive Cards | Written, Azure app registered, no backend |
| Dashboard (`web/render-dashboard`) | Static HTML generator | Running on GitHub Pages, read-only |
| Agent invocation | **NOT BUILT** | This is the core of self-hosting |
| Bootstrap CLI (`bin/os`) | 722 lines | FROZEN — do not extend |
| Signal protocol (`docs/signal-protocol.md`) | 576 line spec | FROZEN — do not build tooling |
| Version alignment | VERSION + os-check | FROZEN — do not extend |

### Critical Path (from architecture.md, annotated with status)

```
1. Architecture doc              ✅ DONE (docs/architecture.md, 844 lines)
2. Move renderer to os/web/      ✅ DONE (web/render-dashboard)
3. Extract dashboard config       ✅ DONE (web/dashboard-config.yml)
4. API layer MVP                  ⚠️  CODE EXISTS, NEVER RUN (api/main.py)
5. Teams bot MVP                  ⚠️  CODE EXISTS, NEVER RUN (bot/)
6. GitHub Actions write-back     ❌ NOT DONE
7. Agent invocation              ❌ NOT DONE ← THE WHOLE POINT
```

### Key Infrastructure Details

- **Azure bot app ID**: feccdf4f-de6a-4a38-b8c0-ea1487c2cf93 (manifest sideloaded, pinned in Teams)
- **Credentials**: `.env` file in repo root (gitignored) — AZURE_APP_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET
- **Dashboard**: dashboard.3dl.dev (GitHub Pages, private repo at ~/projects/dashboard/)
- **API target URL**: localhost:3131 (Phase 1, local), atom.3dl.dev (Phase 2, VPS)
- **Agent specs live in 3DL**: ~/projects/3dl/docs/agent-*.md (7 agents: CEO, CFO, Strategist, Counsel, CPEO, CIO, Marketing)
- **Agent routing table design**: see architecture.md "Agent Routing" section — org-configurable task-type → tier/agent mapping

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
├── api/
│   ├── main.py            # FastAPI server — thin REST wrapper around bd
│   └── projects.yml       # Project registry for API
├── bot/
│   ├── app.py             # aiohttp web server (Teams bot entry point)
│   ├── bot.py             # Command parsing + handlers
│   ├── cards.py           # Adaptive Card builders
│   ├── api_client.py      # Async client for Atom API
│   ├── config.py          # Config from env vars
│   └── test_bot.py        # Unit tests (mocked)
├── web/
│   ├── render-dashboard   # Static site generator (beads → HTML)
│   ├── style.css          # Desert Tech design system
│   └── dashboard-config.yml # Dashboard section config
├── docker/
│   ├── Dockerfile.beads   # Alpine + beads CLI
│   ├── Dockerfile.gh      # Alpine + GitHub CLI
│   ├── Dockerfile.api     # Python + FastAPI
│   └── docker-compose.yml # Service definitions
├── bin/
│   ├── bd                 # Beads CLI wrapper (→ ~/.local/bin/)
│   ├── gh                 # GitHub CLI wrapper (→ ~/.local/bin/)
│   ├── atom-api           # API server start/stop/logs
│   ├── atom-bot           # Teams bot start/stop/logs
│   ├── os                 # Bootstrap CLI (FROZEN)
│   └── os-check           # Version compliance (FROZEN)
├── docs/
│   ├── architecture.md    # THE founding design doc (read, don't rewrite)
│   ├── signal-protocol.md # Cross-repo comm spec (FROZEN tooling)
│   ├── cross-project-protocol.md
│   ├── spin-up-protocol.md
│   └── bootstrap-config.md
├── template/              # Project skeleton (new-project.sh)
├── claude/
│   └── CLAUDE.md          # User-level instructions (→ ~/.claude/)
├── .env                   # Azure credentials (gitignored)
├── setup.sh               # Machine bootstrap
├── new-project.sh         # Scaffold new project
└── .beads/                # Beads database (git-tracked)
```

## Project-Specific Rules

1. **Project-agnostic only**: Nothing in this repo should reference a specific project. If you're writing something that only applies to Aerocloak (or any other project), it belongs in that project's repo.
2. **Backward compatibility**: Changes to `claude/CLAUDE.md`, `docker/`, or `bin/` must not break existing projects. Always run the compatibility check.
3. **Template is forward-only**: Don't try to auto-update existing projects when the template changes. Create project-specific beads if backporting is needed.
4. **Test wrappers after changes**: After modifying `bin/` or `docker/`, verify `bd --version` and `gh --version` work from an existing project directory.
