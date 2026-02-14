# Four Communication Channels

**Status**: Reference document
**Date**: 2026-02-14
**Layer**: OS (architecture reference)

## Overview

The AI Enterprise OS has four communication channels. Three are human-facing surfaces. One is the machine backplane.

```
                    HUMAN
                      |
         +-----------+-----------+
         |           |           |
    1. Console   2. Web     3. Teams
    (CLI)        (Dashboard) (Bot)
         |           |           |
         +-----------+-----------+
                      |
              +--------------+
              |   bd / API   |
              +--------------+
                      |
              4. Signals
              (Agent <-> Agent)
              (Project <-> Project)
```

## Channel 1: Console (Flynn)

**Human <-> System. Change the system.**

| Property | Value |
|----------|-------|
| Interface | Terminal, Claude Code sessions |
| Identity | OS user (filesystem) |
| Permission | Root (all operations) |
| Persistence | Ephemeral (session-scoped) |
| Metaphor | "Flynn's interface to the grid" |

**What happens here**: Architecture decisions, agent spec edits, CLAUDE.md changes, deep analysis work, system configuration. Everything that changes the system itself.

**What does NOT happen here**: Routine status checks, approvals, staff queue management (use Teams/Web for those).

**Tools**: `bd` (direct), `atom` CLI wrapper, Claude Code.

## Channel 2: Web (Dashboard)

**Human <-> Workflow. See and act on work.**

| Property | Value |
|----------|-------|
| Interface | Browser (GitHub Pages -> VPS) |
| Identity | GitHub OAuth (future: Tailscale network auth) |
| Permission | Operator (role-based) |
| Persistence | Always available |
| Metaphor | Mission control display |

**What happens here**: Staff reviews deliverables, approves work, provides feedback. Visual overview of portfolio, staff queue, bead state. Read-heavy with targeted writes (approve, comment, change status).

**What does NOT happen here**: System changes, deep analysis, real-time conversation.

**Evolution**: Static HTML (Phase 1) -> Interactive cards + API (Phase 2) -> Server-rendered + real-time (Phase 3).

## Channel 3: Teams (Atom Bot)

**Human <-> Agents. Conversational operations.**

| Property | Value |
|----------|-------|
| Interface | Microsoft Teams tenant, single "Atom" bot |
| Identity | Tenant membership |
| Permission | Operator (role-based) |
| Persistence | Persistent (Teams retains threads) |
| Metaphor | Executive team chat |

**What happens here**: CEO sessions, board meetings, staff queue management, agent Q&A, approvals, status checks. Natural language interaction with AI executive team. Real-time notifications for urgent items.

**What does NOT happen here**: System changes (bot refuses, points to console). Complex visual analysis (bot links to dashboard).

**Key design**: One bot, multi-agent routing. Channel implies agent (#cfo -> CFO). Intent detection for ambiguous requests. Reactions as lightweight actions.

## Channel 4: Signals (Machine Backplane)

**Agent <-> Agent. Project <-> Project. Internal nervous system.**

| Property | Value |
|----------|-------|
| Interface | bd commands (`bd signal`, `bd inbox`, `bd sweep`) |
| Identity | Repo identity (signal.from field) |
| Permission | Read-only cross-repo, write to own repo only |
| Persistence | Git-backed (beads) |
| Metaphor | Nerve impulses |

**What happens here**: Cross-project coordination. One repo requests work from another. Agents notify each other of completed work. Projects query each other for information/decisions. Staff-signals request human action.

**What does NOT happen here**: Human interaction (signals escalate to channels 1-3 when humans need to be involved).

**Signal types**: staff-signal, request, notify, query.

**Full spec**: `docs/signal-protocol.md`

## Channel Relationships

### Escalation (Channel 4 -> Channels 1-3)

Signals stay machine-to-machine by default. They escalate to human channels when:

| Condition | Escalates To |
|-----------|-------------|
| staff-signal (always) | Teams (#staff-queue) + Web |
| P0 signal | Teams (#alerts) |
| Request, no ack after 48h | Teams (#alerts) |
| Query, needs founder decision | Teams (#command) + Web |
| Any signal marked needs-human | Teams (#alerts) + Web |

### Handoffs Between Human Channels

| From | To | Trigger |
|------|-----|---------|
| Teams -> Web | Bot posts dashboard link for complex visuals |
| Teams -> Console | Bot refuses system change, points to terminal |
| Web -> Teams | "Ask about this" button deep-links to Teams |
| Console -> Teams | Agent posts exec log entry, auto-notifies in Teams |
| Console -> Web | Dashboard auto-renders from bead state |

### Single Source of Truth

All four channels read and write the same state: **beads**. There is no channel-specific state. Beads are the single source of truth; channels are projections.

```
Console --\
Web -------+---> bd (beads CLI) ---> .beads/ (SQLite + JSONL + git)
Teams ----/           ^
Signals -/            |
                 Single write path
```

## When to Use Which Channel

| Task | Channel | Why |
|------|---------|-----|
| Edit agent spec | Console | System change, needs git |
| Review CFO runway model | Web | Visual, read-heavy |
| Ask CEO for status update | Teams | Conversational, quick |
| Request os repo to move a file | Signal | Cross-project, agent-to-agent |
| Approve a decision | Teams or Web | Either works (reaction or button) |
| Deep architecture design | Console | Opus-tier, long context, system-changing |
| Check staff queue | Teams or Web | Quick view (Teams), detailed view (Web) |
| Notify website repo of blog post | Signal | Cross-project FYI |
| Board meeting | Teams | Multi-agent conversation, threaded |
| Sign legal documents | Staff-signal -> Teams + Web | Needs human, pre-packaged |

## Layer Ownership

| Channel | OS Provides | Org Configures |
|---------|-------------|----------------|
| Console | `bd` CLI, session conventions | Agent specs, CLAUDE.md, authority tiers |
| Web | Renderer, templates, API server | Dashboard sections, design system, query definitions |
| Teams | Bot framework, event handlers, routing engine | Channel list, agent routing table, notification rules |
| Signals | `bd signal/inbox/sweep/ack/resolve`, discovery mechanism | Project registry, escalation thresholds, routing defaults |

The OS layer is domain-agnostic. It provides the channel infrastructure. The organization layer configures behavior.
