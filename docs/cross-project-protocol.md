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

## CEO Cross-Project Sweep

Added to the CEO's session protocol in 3dl. Runs at session open.

### Procedure

For each spoke repo in the project registry:

```bash
cd /home/baron/projects/<repo-dir>
bd list --json | python3 -c "
import json, sys
beads = json.load(sys.stdin)
signals = [b for b in beads if b.get('status') == 'open' and b.get('title','').startswith('STAFF-SIGNAL:')]
high_pri = [b for b in beads if b.get('status') == 'open' and b.get('priority', 99) <= 1]
for s in signals: print(f'SIGNAL: {s[\"id\"]} - {s[\"title\"]}')
for h in high_pri: print(f'P{h[\"priority\"]}: {h[\"id\"]} - {h[\"title\"]}')
" 2>/dev/null
```

### What the Sweep Catches

1. **Staff signals**: Open `STAFF-SIGNAL:` beads → import to 3dl staff queue
2. **High-priority work**: P0/P1 open beads → CEO awareness, may trigger cross-project prioritization
3. **Publish-ready posts**: Blog posts with editorial approval → trigger Stage 3 handoff

### Sweep Output

The CEO reports findings at session open:
- New staff signals found (and imports them)
- High-priority spoke work that may need attention
- Any cross-project conflicts or dependencies surfaced

If nothing found, no report needed. Don't waste tokens on "no signals found."
