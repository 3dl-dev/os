# Cross-Project Coordination Protocol

> Reference document for multi-repo coordination across the 3DL portfolio. The enforceable conventions are in `~/.claude/CLAUDE.md` (OS-level); this document provides full context and rationale.

## Model

**Hub-and-spoke.** 3DL (`3dl/`) is the holding company hub. All other project repos are spokes. The 3DL CEO agent is the coordination point — it sweeps spoke repos for signals, manages the canonical staff queue, and owns cross-project prioritization.

Spokes are autonomous: they run their own beads, their own agents, their own sessions. They don't write to other repos. Coordination happens through conventions (naming, labels) and the CEO sweep.

## Project Registry

| Repo Dir | Bead Prefix | Description |
|----------|-------------|-------------|
| `3dl` | `3dl-` | Holding company — strategy, operations, executive team |
| `website` | `website-` | Public website (3dl.dev / thirdiv.com), GitHub Pages |
| `mag-shield` | `mag-shield-` | Aerocloak / magnetic shielding research |
| `galtrader` | `galtrader-` | GalTrader game project |
| `vms` | `vms-` | VMS emulator (lowest-priority spoke) |

All repos live under `/home/baron/projects/`.

## Staff-Signal Convention

When a spoke project identifies work that requires human action (the founder), it creates a **staff-signal bead** in its own repo. The 3DL CEO sweep picks these up and creates canonical `staff-queue` beads in the 3dl repo.

### Creating a Staff Signal

In any spoke repo:

```bash
bd create "STAFF-SIGNAL: <action description>" -p <priority>
```

**Rules:**
- Title MUST start with `STAFF-SIGNAL:` prefix (exact, case-sensitive)
- Description MUST include:
  - **What**: The specific human action needed
  - **Why**: Context for why this can't be handled by agents
  - **Pre-packaged**: Everything the founder needs to execute (links, commands, templates, etc.)
  - **Estimated time**: How long the founder action should take
- Priority reflects urgency from the spoke's perspective; the CEO may reprioritize when importing to the canonical staff queue

### CEO Sweep (Consumer Side)

The 3DL CEO sweep scans all spoke repos for open `STAFF-SIGNAL:` beads. For each:
1. Create a canonical `staff-queue` bead in 3dl with cross-reference to the source
2. Package it per 3dl's staff queue standards
3. Close the spoke's signal bead with reason: `Imported to 3dl staff queue as <3dl-bead-id>`

This keeps spoke repos clean and the canonical queue in one place.

## Cross-Project References

When a bead in one repo references work in another, use the convention:

```
<repo-dir>/<bead-id>
```

Examples:
- `galtrader/galtrader-d0a` — references bead galtrader-d0a in the galtrader repo
- `3dl/3dl-abc` — references bead 3dl-abc in the 3dl repo
- `website/website-123` — references bead website-123 in the website repo

Use these in bead descriptions, exec log entries, and any cross-repo documentation. This is a human-readable convention, not a machine link — the reader navigates to the referenced repo and runs `bd show <bead-id>`.

## Publishing Handoff (3dl to website)

Blog content is authored in 3dl's blog pipeline (`3dl/docs/blog/`) and published to the website repo (`website/`). This is a cross-repo handoff, not a monorepo operation.

### Pipeline

1. **Stages 1-2** (in 3dl): Candidate selection, drafting, editorial review — per 3dl's blog pipeline in `3dl/CLAUDE.md`
2. **Stage 3** (cross-repo): Marketing agent reads the approved post from `3dl/docs/blog/posts/<slug>.md`, converts to HTML, writes to `website/blog/<slug>.html`, updates `website/blog.html` index, commits and pushes in the website repo
3. **Stage 4**: Backdate if needed — displayed date matches when the work happened

### Handoff Mechanics

The Marketing agent (running in a 3dl session) reads from the 3dl repo and writes to the website repo at `/home/baron/projects/website/`. It:
- Reads the approved markdown from `docs/blog/posts/<slug>.md`
- Matches existing website chrome (nav, palette, typography)
- Writes HTML to `/home/baron/projects/website/blog/<slug>.html`
- Updates the blog index at `/home/baron/projects/website/blog.html`
- Commits in the website repo with a message referencing the 3dl blog bead
- Closes the 3dl blog bead with reason: "Published to website"

## Cross-Project Sweep

The `os sweep` command replaces the manual CEO sweep script. It uses the org registry (`os.yml`) for project discovery.

```bash
os sweep                     # signals + P0/P1 across all repos
os sweep --signals-only      # just pending signals
os sweep --json              # machine-parseable output
```

### What the Sweep Catches

1. **Staff signals**: Open `STAFF-SIGNAL:` beads → import to org staff queue
2. **High-priority work**: P0/P1 open beads → CEO awareness, cross-project prioritization
3. **Signal protocol beads**: `SIGNAL(type):` beads (see `docs/signal-protocol.md`)

### Using the Sweep

At session open, run `os sweep`. If items are found:
- Import new staff signals to the org staff queue
- Note high-priority spoke work that may need attention
- Check for cross-project conflicts or dependencies

If nothing found, no report needed.

## Signal Protocol

The generalized cross-repo communication protocol extends STAFF-SIGNAL to four signal types: `staff-signal`, `request`, `notify`, `query`. Full spec: `docs/signal-protocol.md`.

Key principle: every repo is sovereign. No repo writes to another repo's `.beads/`. Communication is through signal beads discovered via pull-based scanning (`os sweep`, `bd inbox`).

## Project Discovery

Project paths are discovered via `os.yml` (in the org repo) and `os.conf` (machine-local registry). See `docs/bootstrap-config.md` for the full spec.

```bash
os projects              # list all projects
os projects --json       # machine-parseable
os status                # show orgs + project alignment
```

This replaces hardcoded project registry tables. Tools (dashboard renderer, API server, Teams bot) use `os projects` for discovery.
