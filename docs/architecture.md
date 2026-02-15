# AI Enterprise OS Architecture

**Status**: Founding architecture document
**Date**: 2026-02-14
**Context**: CEO/founder architectural conversation → product documentation

## Executive Summary

The AI Enterprise OS is a three-layer system where AI agents manage organizational workflows and humans interact through three surfaces (console, web, Teams). The architecture separates domain-agnostic infrastructure (OS layer) from organization-specific policy (organization layer) from individual workloads (projects layer).

**Core principles:**
- **Beads are the single source of truth** — all state lives in git-backed beads, not databases
- **AI is the management backplane** — Claude agents coordinate work, humans approve/execute
- **GitHub is the center of gravity** — repos (state), Actions (compute), Pages (UI), API (programmatic access)
- **Minimal infrastructure** — ~$85-130/mo total cost (mostly Claude API, $7-10/mo hosting)
- **Dog-food from day 1** — build the OS using the OS

## Three-Layer Model

### Layer 1: OS (Platform)

Domain-agnostic infrastructure. Does not know about any specific organization's agents, authority tiers, or workflows.

**Provides:**
- `bd` — state machine CLI for tracking work (beads)
- REST API — thin wrapper around `bd` for remote access
- Web renderer — turns bead state into HTML dashboards
- Teams bot — conversational interface to bead state
- Docker conventions — how projects containerize tools
- Session conventions — how Claude Code sessions bootstrap and manage context
- Cross-project protocol primitives — STAFF-SIGNAL as a protocol, not a policy
- GitHub Actions workflows — compute layer for async operations

**Lives in:** `/home/baron/projects/os/`

**Key insight:** OS is the kernel. It provides services, not policies. An organization configures the OS to implement its management model.

### Layer 2: Organization (Policy and Management)

Domain-specific policy layer. Defines WHO does WHAT and HOW decisions are made.

**Contains:**
- Agent specs defining roles and routing rules (`docs/agent-*.md`)
- CLAUDE.md defining workflows, cascades, authority tiers
- Executive log recording decisions (`docs/exec-log/<agent>/`)
- Company vision and strategic direction (`docs/company-vision.md`)
- Configuration consumed by OS layer (dashboard layout, section definitions, queue semantics)

**Lives in:** `/home/baron/projects/3dl/` (reference implementation)

**Analogy:** The organization layer is like `/etc/` on Linux — it configures how the kernel behaves for this specific org. OS is the kernel, organization is the policy.

### Layer 3: Projects (Workloads)

Individual repos managed by the organization. Each has:
- Own `.beads/` for work tracking
- Own `CLAUDE.md` with project-specific rules
- Own `docker-compose.yml` for project tools
- Follows OS conventions, doesn't know about org-level management

**Lives in:** `/home/baron/projects/{galtrader,vms,mag-shield,website}/` (example spokes)

**Interaction:** Projects use OS primitives directly (`bd`, Docker conventions). Organization coordinates across projects via cross-project protocol (CEO sweep, STAFF-SIGNAL).

## Interfaces Between Layers

### OS → Organization
OS provides services, organization provides configuration.

- Web renderer reads org's `config/dashboard.yml` (or equivalent) to know what sections to show
- Teams bot reads org's agent specs (`docs/agent-*.md`) to route messages
- OS doesn't import org policy; org configures OS through well-defined config files

**Key constraint:** OS layer must remain domain-agnostic. No hardcoded references to "CEO" or "3DL" or "staff queue" — those are organization concepts.

### Organization → Projects
Policy and coordination.

- Cross-project protocol (CEO sweep imports STAFF-SIGNAL beads from spoke repos)
- Project CLAUDE.md inherits conventions from org CLAUDE.md
- Projects don't import org agent specs; they just create beads and signals
- Organization agents read project beads to coordinate work

**Key constraint:** Projects shouldn't need to know about the organization's agent roster. The CEO sweep is pull-based, not push-based.

### OS → Projects
Direct primitive access.

- Projects use `bd` for state management
- Projects use Docker conventions for tooling
- Projects follow session conventions for Claude Code integration

**Key constraint:** These primitives must work standalone. A project can use `bd` without an organization layer.

## Three Interaction Surfaces

```
┌─────────────────────────────────────────────────────┐
│                  INTERACTION SURFACES                │
├─────────────────┬─────────────────┬─────────────────┤
│   Console       │   Web           │   Teams         │
│   (CLI)         │   (Dashboard)   │   (Bot)         │
│                 │                 │                 │
│ "Flynn's Grid"  │ Visual workflow │ Conversational  │
│ Full access     │ Staff reviews   │ Always-on ops   │
│ Deep work       │ Deliverables    │ Real-time       │
│ Ephemeral       │ Always available│ Persistent      │
└────────┬────────┴────────┬────────┴────────┬────────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────▼──────────┐
                │  OS API Server      │
                │  (bd wrapper)       │
                └──────────┬──────────┘
                           │
                ┌──────────▼──────────┐
                │  bd (beads CLI)     │
                │  SQLite + JSONL     │
                │  git-backed         │
                └─────────────────────┘
```

### 1. Console (CLI)

**Interface:** Terminal, Claude Code sessions
**Auth:** OS user (filesystem)
**Permissions:** Root (all operations)
**Use case:** Deep work, system changes, architecture decisions

"Flynn's interface to the grid." Full system access. Where you change the system itself (agent specs, OS config, architecture). Ephemeral, per-repo, deep work sessions.

**Tools:**
- `bd` — direct state machine access
- `atom` wrapper — shortcuts for common multi-step operations (CEO session, staff queue, approval flows)
- Claude Code — AI pair programming environment

**No changes needed.** Console is the root surface — all other surfaces are projections of the same state.

### 2. Web (Dashboard)

**Interface:** Browser, static HTML + client-side JS
**Auth:** GitHub OAuth (future; Tailscale network-level auth initially)
**Permissions:** Role-based (operator tier for staff)
**Use case:** Staff reviews deliverables, approves work, provides feedback

Visual workflow + document presentation. Read-write via GitHub Actions write-back. Always available (GitHub Pages). The primary way staff sees AI team output.

**Evolution:**
- **Phase 1 (current):** Static HTML generated by `render-dashboard`. Read-only. GitHub Pages.
- **Phase 2 (Atom v1):** Static HTML + client-side JS calling API for writes. Interactive cards (expand, comment, change status). Still GitHub Pages.
- **Phase 3 (Atom v2):** Server-rendered pages from API server. Real-time updates via SSE. Hosted on VPS alongside API.

**Design system:** Desert Tech (extends website's design: same fonts, colors, card patterns).

### 3. Teams

**Interface:** Microsoft Teams tenant, conversational bot
**Auth:** Teams/Azure OAuth (tenant membership)
**Permissions:** Role-based (operator tier for staff)
**Use case:** Board meetings, CEO sessions, task management, real-time communication

Conversational operations. Agents communicate with staff. Real-time, always-on (Teams bot on Azure Functions or Fly.io). Points to web for visual content.

**Evolution:**
- **Phase 1:** Slash commands only (`/atom status`, `/atom staff`, `/atom show <id>`)
- **Phase 2:** Bot posts to channels (CEO session summaries, staff queue updates, gate notifications). Founder replies in-thread.
- **Phase 3:** Full conversational AI. Natural language intent → Claude interprets → `bd` commands → confirmation.

**Hosting:** Azure Functions (potentially free tier) or Fly.io (~$5/mo) for persistent Teams bot process.

## Permission Model

```
┌─────────┬──────────────────┬──────────────┬────────────────────┐
│ Surface │ Identity         │ Auth Method  │ Permission Tier    │
├─────────┼──────────────────┼──────────────┼────────────────────┤
│ Console │ OS user (baron)  │ Filesystem   │ root (all ops)     │
│ Web     │ GitHub user      │ OAuth2       │ operator/viewer    │
│ Teams   │ Tenant member    │ Teams OAuth  │ operator           │
│ API     │ Service account  │ Bearer token │ scoped (agents)    │
└─────────┴──────────────────┴──────────────┴────────────────────┘
```

**Permission tiers:**
- **root:** Everything — create, update, close, config, sync, admin (console user only)
- **operator:** Create, update, close beads. Add comments. Resolve gates. Invoke AI. (staff via web/Teams)
- **viewer:** Read beads, activity, dashboard. No writes. (board observers, future)
- **agent:** Write beads scoped to their role. Comments. State changes. (AI agents via API tokens)

**Audit trail:** Every API write records the actor: `bd update <id> --actor "baron:web"`. The `--actor` flag is already supported by `bd`.

## State Model

### Single Source of Truth: Beads

All state lives in beads. All surfaces read/write beads. No dual-write. Beads are git-backed JSONL + SQLite in each repo's `.beads/` directory.

```
State hierarchy:
1. bd (beads CLI) — single write path, all surfaces call bd
2. SQLite + JSONL — in-repo storage (.beads/)
3. Git — system of record (JSONL files are git-tracked)
4. GitHub — remote persistence, coordination point
```

**What `bd` already provides** (inventory before extending):
- CRUD: create, show, update, close, list, query
- Dependencies: dep add/remove, graph, dep tree
- Comments/threads: `bd comments add <id> "text"`
- State dimensions: `bd set-state <id> dim=val` (labels + event beads)
- Custom statuses: `bd config set status.custom "..."`
- Gates (async waits): human, timer, gh:run, gh:pr, bead types
- Activity feed: `bd activity --follow --town`
- Swarm (parallel work): `bd swarm create/status/validate`
- KV store: `bd kv set/get` — per-project persistent flags
- Labels, types, metadata, estimates, due dates, defer, external refs, spec links

**Key insight:** Most "state extensions needed" are already built into `bd`. The work is not extending `bd` — it is (a) defining conventions for which features to use and how, (b) wrapping `bd` in an API, and (c) building the surface clients.

### Workflow States

Beyond `bd`'s built-in states (`open, in_progress, blocked, deferred, closed`), define custom statuses:

```bash
bd config set status.custom "needs-guidance,in-review,approved,blocked-on-staff,scheduled"
```

**State machine:**

```
                    ┌─────────┐
          create───►│  open   │
                    └────┬────┘
                         │ claim / assign
                    ┌────▼────┐
             ┌──────┤in_progress├──────┐
             │      └────┬────┘       │
             │           │            │
        ┌────▼─────┐ ┌───▼──────┐ ┌──▼──────────┐
        │ blocked  │ │in-review │ │needs-guidance│
        └────┬─────┘ └───┬──────┘ └──┬───────────┘
             │           │           │
             │      ┌────▼────┐      │
             └─────►│approved │◄─────┘
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
        ┌─────▼──────┐ ┌▼────┐ ┌──▼────┐
        │blocked-on- │ │closed│ │deferred│
        │staff       │ └─────┘ └───────┘
        └─────┬──────┘
              │ staff completes
              ▼
           closed
```

**State definitions:**

| Status | Meaning | Who acts |
|---|---|---|
| `open` | Created, not started | Anyone |
| `in_progress` | Agent or human working on it | Assigned agent |
| `blocked` | Waiting on a dependency bead | System (dep resolution) |
| `needs-guidance` | Agent hit a decision point, needs founder input | Founder |
| `in-review` | Work done, awaiting review | Founder |
| `approved` | Founder approved, ready for execution/close | Agent or founder |
| `blocked-on-staff` | Needs human physical-world action | Founder |
| `scheduled` | Approved, queued for a specific time window | System |
| `deferred` | Parked, hidden until defer date | System |
| `closed` | Done | N/A |

### State Dimensions

Beyond status, use state dimensions for operational metadata that can change independently:

```bash
bd set-state <id> surface=web --reason "Created via web dashboard"
bd set-state <id> agent=ceo --reason "CEO claimed this task"
bd set-state <id> tier=opus --reason "Escalated to Opus for strategic decision"
```

**Standard dimensions:**

| Dimension | Values | Purpose |
|---|---|---|
| `surface` | cli, web, teams | Where the bead was last mutated from |
| `agent` | ceo, cfo, counsel, strategist, cpeo, cio, marketing | Which AI agent owns execution |
| `tier` | haiku, sonnet, opus | Model tier for AI work on this bead |

### Labels Convention

Standardize label namespaces:

| Prefix | Example | Purpose |
|---|---|---|
| `staff-queue` | (no prefix, bare label) | Marks a staff queue item |
| role name | `ceo`, `cfo`, `counsel` | Owning agent role |
| `project:` | `project:mag-shield` | Cross-project reference |
| `type:` | `type:decision`, `type:staff-signal` | Semantic type beyond bd's built-in types |
| `topic:` | `topic:entity`, `topic:tax` | Subject area for filtering |

### Gates for Staff Boundary

Gates are the mechanism for managing the staff boundary. When AI work reaches the one-yard line:

```bash
bd gate add-waiter <staff-bead-id> --type human
```

The gate blocks downstream beads until the founder resolves it. The web dashboard surfaces open human gates prominently. Teams notifies when gates are created.

### Comments for Threads

`bd comments add <id> "text"` already exists. Convention:

- Agents prefix comments with `[AGENT:<role>]` — e.g., `[AGENT:CEO] Reprioritized to P1 based on consulting timeline.`
- Founder comments have no prefix (or `[FOUNDER]` if coming via Teams/web for attribution).
- Surface prefix: `[via:web]`, `[via:teams]` — appended automatically by the API layer.

## API Layer

### Decision: Thin HTTP API wrapping `bd`

**Not** direct `bd` CLI calls from web/Teams. **Not** GraphQL. A thin REST API that shells out to `bd`.

**Rationale:**

| Option | Latency | Auth | Complexity | Verdict |
|---|---|---|---|---|
| Direct `bd` from each surface | Fast (local) | None (filesystem) | Duplicated logic | CLI only |
| REST API wrapping `bd` | ~50-100ms overhead | Token-based | Minimal | **Chosen** |
| GraphQL wrapping `bd` | Same as REST | Same | Over-engineered | No |
| GitHub Actions as compute | 10-30s cold start | GitHub auth | Good for async, bad for reads | Supplement |

The API server is a lightweight process (Python or Go) that:
1. Accepts HTTP requests
2. Validates auth
3. Translates to `bd` CLI calls
4. Returns JSON

It runs on the same machine as `bd` (founder's workstation or small VPS). No cloud infrastructure.

### API Design

Base URL: `http://localhost:3131/api/v1` (local dev) or `https://atom.3dl.dev/api/v1` (production).

**Read endpoints (GET):**

```
GET  /beads                    → bd list --json [+ query params]
GET  /beads/:id                → bd show <id> --json
GET  /beads/:id/comments       → bd comments <id> --json
GET  /beads/:id/deps           → bd dep tree <id> --json
GET  /beads/:id/state/:dim     → bd state <id> <dim>
GET  /activity                 → bd activity --json [--since, --limit]
GET  /activity/stream          → SSE (bd activity --follow --json)
GET  /gates                    → bd gate list --json
GET  /projects                 → iterate repos, bd list --json per repo
GET  /projects/:name/beads     → bd list --json --db <repo>/.beads/*.db
GET  /staff-queue              → bd query "label=staff-queue AND status!=closed" --json
```

**Write endpoints (POST/PATCH/DELETE):**

```
POST   /beads                  → bd create "title" [flags]
PATCH  /beads/:id              → bd update <id> [flags]
POST   /beads/:id/close        → bd close <id> --reason "..."
POST   /beads/:id/claim        → bd update <id> --claim
POST   /beads/:id/comments     → bd comments add <id> "text"
POST   /beads/:id/state        → bd set-state <id> dim=val
POST   /beads/:id/labels       → bd label add <id> <label>
DELETE /beads/:id/labels/:name → bd label remove <id> <label>
POST   /gates/:id/resolve      → bd gate resolve <id>
```

**Cross-project reads:**

```
GET  /sweep                    → CEO sweep results (cached, refreshed on demand)
POST /sweep/refresh            → Force re-scan all spoke repos
```

### Implementation: Single-file Python server

FastAPI or plain `http.server` — a single Python file that:
- Parses routes
- Shells out to `bd` with `subprocess.run`
- Returns JSON
- Handles auth via bearer token or GitHub OAuth callback

**Why Python:** Already in use for `render-dashboard`. No new runtime. stdlib `subprocess` + `json` is all that's needed. FastAPI adds OpenAPI docs for free.

**Why not Go:** `bd` is Go, but the API layer is a thin shim, not performance-critical. Python is faster to iterate on.

```python
# Pseudocode structure
@app.get("/api/v1/beads")
async def list_beads(status: str = None, priority: int = None, label: str = None):
    cmd = [BD, "list", "--json", "--no-daemon"]
    if status: cmd += ["--status", status]
    # ... etc
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_PATH)
    return json.loads(result.stdout)
```

### Deployment

**Phase 1 (self-hosted):** Run on the founder's workstation. Tailscale for remote access. No public exposure.

**Phase 2 (production):** Small VPS (Hetzner, $5/mo). Caddy for TLS on `atom.3dl.dev`. The API server + `bd` + git repos all on the same box. The `bd` daemon handles git sync.

**Phase 3 (multi-tenant):** Not in scope. Atom is a single-tenant system. If productized later, each tenant gets their own instance.

## Agent Invocation Model

### Three Tiers

```
┌────────────────────────────────────────────────┐
│ Tier 0: Data Only (no AI)                      │
│ bd list, bd show, bd query — pure CRUD         │
│ Cost: $0   Latency: <100ms                     │
├────────────────────────────────────────────────┤
│ Tier 1: Fast AI (Haiku)                        │
│ Summarize bead, answer status question,        │
│ generate comment, triage priority               │
│ Cost: ~$0.001/call   Latency: 1-3s             │
├────────────────────────────────────────────────┤
│ Tier 2: Deep AI (Sonnet)                       │
│ Draft exec log entry, analyze dependencies,     │
│ research task, structured analysis              │
│ Cost: ~$0.01/call   Latency: 5-15s             │
├────────────────────────────────────────────────┤
│ Tier 3: Strategic AI (Opus)                    │
│ CEO session, strategy decisions, cross-project  │
│ synthesis, novel design                         │
│ Cost: ~$0.10/call   Latency: 15-60s            │
└────────────────────────────────────────────────┘
```

### Dispatch Mechanism

The API server does NOT run Claude directly. It dispatches to a job queue.

```
Surface → API → Job Queue → Worker → Claude API → bd writes → Response
```

**Job queue options (in order of preference):**

1. **In-process async (Phase 1):** Python `asyncio` task. The API server spawns an async task, calls Claude API, writes results back via `bd`. Polling or SSE for status. Good enough for single-user.

2. **File-based queue (Phase 2):** Drop a JSON file in `.beads/jobs/`, worker picks it up. Dead simple. Survives restarts.

3. **Redis/SQLite queue (Phase 3):** Only if job volume justifies it.

**Job schema:**

```json
{
  "id": "job-abc123",
  "tier": "haiku",
  "task": "summarize-bead",
  "context": {
    "bead_id": "3dl-8om",
    "prompt": "Summarize this bead's status and next actions"
  },
  "surface": "teams",
  "requested_by": "baron",
  "created_at": "2026-02-14T17:00:00Z",
  "status": "pending"
}
```

### Agent Routing

The API layer includes a routing table mapping task types to tiers and agent roles:

```python
AGENT_ROUTES = {
    "summarize":        {"tier": "haiku",  "agent": None},
    "triage":           {"tier": "haiku",  "agent": "ceo"},
    "draft-comment":    {"tier": "haiku",  "agent": None},
    "analyze-deps":     {"tier": "sonnet", "agent": "cpeo"},
    "draft-exec-log":   {"tier": "sonnet", "agent": None},
    "research":         {"tier": "sonnet", "agent": "strategist"},
    "ceo-session":      {"tier": "opus",   "agent": "ceo"},
    "strategy-decision":{"tier": "opus",   "agent": "ceo"},
    "design-review":    {"tier": "opus",   "agent": "cpeo"},
}
```

This is organization-specific configuration, not OS layer logic. The OS provides the routing mechanism; the organization defines the routes.

### Claude API Integration

The worker calls the Anthropic API directly (not Claude Code). It constructs system prompts from agent specs (`docs/agent-*.md`) and includes bead context read via `bd show --json`.

```python
# Pseudocode
def execute_job(job):
    agent_spec = read_agent_spec(job["agent"])  # docs/agent-ceo.md etc.
    bead_context = subprocess.run([BD, "show", job["context"]["bead_id"], "--json", ...])

    response = anthropic.messages.create(
        model=TIER_TO_MODEL[job["tier"]],
        system=agent_spec,
        messages=[{"role": "user", "content": job["context"]["prompt"]}]
    )

    # Write results back via bd
    subprocess.run([BD, "comments", "add", job["context"]["bead_id"], response.text, ...])
```

## Autonomous Operation Controls

When agents operate autonomously (triggered by signals, schedules, or chain reactions), the system must prevent runaway execution, infinite feedback loops, and uncontrolled token spend.

### Feedback Loop Prevention

**Depth limits:** Every autonomous chain tracks its depth. A signal that triggers an agent that creates a signal that triggers another agent — each hop increments depth. Hard cap at **depth 5** for any autonomous chain. Reaching the cap halts the chain and creates a `needs-guidance` bead for the CEO.

```
Signal A → Agent 1 (depth 1) → Signal B → Agent 2 (depth 2) → ... → depth 5 → HALT
```

**Cooldowns:** After an autonomous agent completes work, it enters a cooldown before it can be re-triggered by the same signal type. Prevents rapid-fire loops where Agent A's output triggers Agent B, whose output triggers Agent A.

| Tier | Cooldown |
|------|----------|
| Haiku | 60 seconds |
| Sonnet | 5 minutes |
| Opus | 30 minutes |

**Rejection caps:** If a staff member rejects an auto-created task 3 times in a row from the same agent, that agent loses autonomous task-creation privilege until the CEO reviews and re-enables it.

**Circuit breakers:** If any agent produces 3 consecutive errors (API failures, malformed output, bd write failures), it's circuit-broken — all autonomous invocations pause, a `needs-guidance` bead is created, and the system waits for human intervention.

### Token Budget Hierarchy

Token spend is capped at four levels. When any cap is hit, the system pauses autonomous work and surfaces the overage to the founder.

```
Global Monthly Cap ($150 default)
├── Per-Agent Daily Cap
│   ├── CEO:        $5/day
│   ├── CFO:        $2/day
│   ├── Strategist: $3/day
│   ├── Counsel:    $2/day
│   ├── CPEO:      $3/day
│   ├── CIO:        $1/day
│   └── Marketing:  $2/day
├── Per-Event Cap
│   ├── Haiku task:  $0.01
│   ├── Sonnet task: $0.10
│   └── Opus task:   $1.00
└── Per-Chain Cap
    └── Any autonomous chain: $5.00 total
```

**Tracking:** The API server logs token usage per job. `bd kv` stores running totals:

```bash
bd kv get token-budget/2026-02/global          # Month-to-date global spend
bd kv get token-budget/2026-02-14/agent/ceo    # CEO's daily spend
bd kv get token-budget/chain/chain-abc123      # Specific chain's total
```

**Overage behavior:** When a cap is hit, the system:
1. Completes the current job (don't leave partial state)
2. Pauses all autonomous work at that scope
3. Creates a bead: `BUDGET: <scope> cap reached ($X/$Y)`
4. Notifies founder via Teams
5. Resumes only when founder approves (raises cap or acknowledges)

### Opus-Never-Autonomous Rule

**Opus tier is NEVER invoked autonomously.** Opus calls require explicit human initiation — a console session, a Teams command, or a web action. This is a hard architectural constraint, not a policy preference.

Rationale: Opus is the most expensive tier (~$0.10/call) and handles strategic decisions that should always have human oversight. An autonomous loop accidentally escalating to Opus could burn through the monthly budget in minutes.

If an autonomous chain determines it needs Opus-level reasoning, it creates a `needs-guidance` bead and halts.

### System Quiesce

Three operational modes for the autonomous system:

| Mode | Autonomous Work | Human-Initiated | Reads |
|------|----------------|-----------------|-------|
| **Active** | Running | Running | Running |
| **Drain** | Completes in-flight, no new | Running | Running |
| **Quiesce** | Stopped | Running | Running |
| **Sleep** | Stopped | Stopped (queued) | Running |

**Commands:**

```bash
atom quiesce              # Stop all autonomous work immediately
atom drain                # Let in-flight complete, then stop
atom resume               # Return to active mode
atom sleep                # Stop everything except reads
atom wake                 # Return to active from sleep
atom status               # Show current mode + in-flight jobs
```

**Sleep schedules:** Organization-configurable in `config/schedules.yml`:

```yaml
sleep_schedule:
  # No autonomous work outside business hours
  weekdays: "08:00-22:00 America/New_York"
  weekends: "10:00-18:00 America/New_York"
  # Override: always-on for P0 signals
  exceptions:
    - priority: 0
      mode: active
```

**Quiesce is the emergency brake.** If the founder suspects runaway behavior, `atom quiesce` immediately halts all autonomous work while keeping reads functional so the founder can inspect state.

### Autonomous Invocation Rules Summary

| Rule | Constraint |
|------|-----------|
| Depth limit | Max 5 hops per autonomous chain |
| Cooldown | Haiku 60s, Sonnet 5m, Opus 30m between same-type triggers |
| Rejection cap | 3 consecutive staff rejections → agent loses auto-create |
| Circuit breaker | 3 consecutive errors → agent paused |
| Token budget | 4-level hierarchy, hard caps at each level |
| Opus exclusion | Never autonomous — always human-initiated |
| Sleep schedule | Configurable active hours, P0 exceptions |
| Quiesce | Emergency brake, instant halt of all autonomous work |

## Infrastructure & Cost Model

### GitHub as Center of Gravity

GitHub provides:
- **Repos:** State storage (beads in `.beads/`, git-tracked)
- **Actions:** Compute layer (dashboard rendering, automated sweeps, async jobs)
- **Pages:** Web UI hosting (static HTML, free for Team plan)
- **API:** Programmatic access (webhooks, OAuth, repo operations)

**Why GitHub:** Already using it. Free/Team tiers cover most needs. Avoid introducing new infrastructure.

### Storage Architecture

**All state lives in git. No databases.**

| Data | Storage | Location | Cost |
|------|---------|----------|------|
| **Beads state** | SQLite files in `.beads/` | Each project repo, git-tracked | $0 |
| **Exec log entries** | Markdown files | `docs/exec-log/<agent>/` in repos | $0 |
| **Dashboard HTML** | Static HTML/CSS/JS | `dashboard` repo, GitHub Pages | $0 |
| **Teams thread mapping** | Ephemeral or SQLite | Fly.io volume or Redis (256MB free) | $0-1 |
| **Conversation cache** | In-memory | Teams bot process | $0 |

**No managed databases. No S3 buckets. No persistent queues.**

Git is the source of truth. Beads are the state machine. Everything else derives from that.

### Hosting & Cost Breakdown

**Solo founder (baseline):**
- **Claude API:** $75-120/mo (dominant cost — 90% of total spend)
- **Teams bot:** $5/mo (Fly.io small instance or Azure Functions free tier)
- **Web dashboard:** $0 (GitHub Pages + Actions within free tier)
- **API server:** $0 (Phase 1: local Tailscale) or $5/mo (Phase 2: VPS)
- **Storage:** $0 (git-backed beads)

**Total: $85-130/mo**

**Key insight:** The value prop is AI management, not hosting complexity. Keep infrastructure dead simple and spend on model intelligence, not DevOps.

### Scaling Cost Cliffs

- **1 person → 3 people:** ~3x Claude costs ($225-360/mo), hosting unchanged
- **3 people → 10 people:** ~10x Claude costs ($750-1200/mo), potential need for Teams bot upgrade ($20-40/mo more)

**At 10 people:** Atom is significantly cheaper than SaaS alternatives (no per-seat fees). Linear/Notion would be $1000-2000/mo; Atom is $770-1250/mo.

### Cost Optimization Levers

1. **Model routing discipline:** Haiku default, escalate only when needed
2. **Prompt caching:** Reuse beads state, agent specs (50% token savings on input)
3. **Batch API** (50% discount): For non-urgent work (dashboard renders, overnight analysis)
4. **Token budgets per agent type:** Hard caps, enforce in system prompts
5. **Conversation pruning:** Don't send entire thread history every time, just relevant context

**Recommended target:** $75-120/mo for solo founder, actively using Atom.

## Cross-Project Integration

### Multi-Repo Reads

The API server has access to all spoke repos on the filesystem. It reads beads from each repo's `.beads/` directory using `bd --db <path>`.

```
GET /projects/mag-shield/beads → bd list --json --db /home/baron/projects/mag-shield/.beads/*.db
```

### Staff Signal Import

The current CEO sweep is a Python script run manually. The API server automates it:

1. `GET /sweep` returns cached sweep results
2. `POST /sweep/refresh` re-scans all spoke repos
3. Staff signals are surfaced in the web dashboard and Teams
4. The CEO agent (invoked via Tier 3) decides whether to import each signal

### Bead Cross-References

The `<repo>/<bead-id>` convention remains. The API resolves cross-references for display:

```
GET /beads/3dl-8om → includes resolved cross-refs from description
```

## Where Code Lives

```
os/                              # THE PLATFORM
├── bin/
│   ├── bd                       # State machine CLI (wrapper → docker)
│   ├── gh                       # GitHub CLI (wrapper → docker)
│   ├── atom                     # Console shortcuts (CEO session, staff, approve)
│   └── atom-api                 # REST API server (Python/FastAPI)
├── bot/                         # Teams bot
│   ├── main.py                  # Bot Framework SDK + Claude API integration
│   └── Dockerfile               # Fly.io or Azure Functions deployment
├── web/                         # Dashboard renderer + templates
│   ├── render.py                # Static site generator (replaces 3dl's bin/render-dashboard)
│   ├── templates/               # Jinja2 templates for dashboard sections
│   └── static/                  # CSS (Desert Tech design system), JS
├── .github/workflows/           # Actions compute layer
│   ├── render-dashboard.yml     # Scheduled/triggered dashboard rebuild
│   ├── sweep.yml                # Daily cross-project CEO sweep
│   └── deploy-bot.yml           # Deploy Teams bot to Fly.io or Azure on push
├── docker/                      # Shared base images
│   ├── Dockerfile.beads         # Alpine + bd CLI
│   ├── Dockerfile.gh            # Alpine + GitHub CLI
│   └── docker-compose.yml       # Shared services (PROJECT_ROOT-aware)
└── docs/
    ├── architecture.md          # THIS DOCUMENT
    ├── cross-project-protocol.md
    └── session-conventions.md

3dl/                             # AN ORGANIZATION (reference implementation)
├── CLAUDE.md                    # Org policy
├── docs/agent-*.md              # Role definitions
├── docs/company-vision.md       # Strategic direction
├── docs/exec-log/               # Decision record
├── config/
│   ├── dashboard.yml            # Dashboard configuration (what sections, what queries)
│   └── agent-routes.json        # Task type → tier/agent mapping
└── .beads/                      # Org-level work tracking

galtrader/                       # A PROJECT (workload)
├── CLAUDE.md                    # Project rules
├── .beads/                      # Project work
├── docker-compose.yml           # Project tools
└── src/                         # Actual code
```

## What Does NOT Change

- **`bd` is the single write path.** The API server calls `bd`. No direct SQLite writes.
- **Git is the persistence layer.** JSONL files in `.beads/` are git-tracked. The daemon syncs.
- **Agent specs live in `docs/agent-*.md`.** No new agent definition format.
- **Cross-project protocol stays hub-and-spoke.** The API server just automates the CEO sweep.
- **Dashboard design system stays Desert Tech.** Web surface inherits existing CSS.

## Self-Hosting and Product Vision

This system dog-foods itself. As it's built, it runs the organization building it. The OS is both infrastructure and product:

- **Dog-food:** 3DL runs on OS. OS improvements immediately benefit 3DL operations.
- **Product:** OS is the platform offering. "Here's an AI enterprise OS — define your agents, your workflow rules, your authority model, your staff roles. The OS handles state, surfaces, orchestration, and people management."
- **3DL is the reference implementation:** Proof it works, built by using it. One founder, multiple projects, AI executive team, staff queue driving all human work.

## Critical Path

Implementation order, based on dependencies:

1. **Architecture doc** (this document) — design decisions captured
2. **Move renderer from 3dl to os/web/** — make dashboard generation an OS service
3. **Extract dashboard config** (3dl configures what, os renders how) — separate policy from mechanism
4. **API layer MVP** — thin Python wrapper around `bd`, read endpoints only
5. **Teams bot MVP** — conversational interface, messaging extensions, invokes API
6. **GitHub Actions write-back** — web interactions trigger Actions jobs that mutate beads state
7. **Agent invocation** — job queue, Claude API integration, agent routing

## Design Constraints

### Constraint 1: No Vendor Lock-In

All state must be portable. If GitHub disappears tomorrow, the system still works (local git repos, local `bd`, local API server). Only the hosting moves.

### Constraint 2: Minimal Infrastructure

No managed databases. No Kubernetes. No microservices. One small VPS can run the entire system (API + Teams bot + git repos).

### Constraint 3: Token Optimization First

90% of the cost is Claude API. Every architectural decision must consider token impact. Prompt caching is not an afterthought — it's core.

### Constraint 4: Dog-Food Compatibility

Every OS change must work for 3DL immediately. If a feature breaks the reference implementation, it's not ready.

### Constraint 5: Single-Tenant by Design

Atom is not multi-tenant. Each organization gets its own instance (own repos, own API server, own Teams bot). Simplifies auth, deployment, data isolation.

## Build vs. Buy

**Evaluated alternatives:**
- **Linear + wrapper:** Great UI, but vendor lock-in, per-seat fees, not git-backed, no AI-native orchestration
- **Notion + wrapper:** Good for docs, bad for state machine, slow API, vendor lock-in
- **n8n/Windmill:** Workflow metaphor doesn't match AI management backplane, over-engineered

**Verdict: Build Atom.**

**Rationale:**
1. **Cost:** Comparable to alternatives at small scale, cheaper at larger scale (no per-seat fees)
2. **Value alignment:** AI-native, git-backed, multi-project, people management — no existing tool does this
3. **Dog-foodable:** Use it to build itself from day 1
4. **Control:** Define UX, mental model, token optimization strategy
5. **Infrastructure simplicity:** $7-10/mo hosting, no databases, no DevOps complexity

## Sources

This architecture document synthesizes decisions from:
- `/home/baron/projects/3dl/docs/atom-architecture-state-api.md` (state model & API layer design)
- `/home/baron/projects/3dl/docs/atom-infrastructure-cost.md` (hosting & cost analysis)
- `/home/baron/projects/os/CLAUDE.md` (OS layer principles)
- `/home/baron/projects/3dl/CLAUDE.md` (3DL as reference implementation)
- CEO/founder architectural conversation (2026-02-14)
