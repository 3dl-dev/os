# Signal Protocol

**Status**: Design spec
**Date**: 2026-02-14
**Layer**: OS (domain-agnostic primitive)

## Purpose

Signals are the fourth communication channel: agent-to-agent, project-to-project. Channels 1-3 (console, web, Teams) are human-facing surfaces. Channel 4 is the machine backplane -- the internal nervous system of the AI Enterprise OS.

Signals enable cross-repo coordination without violating repo sovereignty. No repo writes to another repo's `.beads/` or files. The sender creates a signal bead in its own repo; the receiver discovers it and acts.

## Core Principles

1. **Repo sovereignty**: Every repo owns its own `.beads/`. No cross-writes.
2. **Sender packages**: The signal carries everything the receiver needs to act (one-yard-line principle).
3. **Pull-based discovery**: Receivers scan for signals addressed to them. No push mechanism required.
4. **Bead-native**: Signals ARE beads -- not a parallel system. They use bd's existing type system, labels, metadata, state dimensions, and gates.
5. **Escalation path**: Machine signals can escalate to human channels when needed.

## Signal Types

Four types. This is the minimal complete set.

| Type | Direction | Meaning | Example |
|------|-----------|---------|---------|
| `staff-signal` | project -> org | Needs human action | "Sign LLC docs" |
| `request` | any -> any | "Please do X" | "Move renderer to os/web/" |
| `notify` | any -> any | "FYI, I did X that affects you" | "Published blog post, update index" |
| `query` | any -> any | "I need info/decision from you" | "What auth model should I use?" |

**Why not more types?** Every cross-repo interaction is one of: "do something" (request), "I did something" (notify), "answer something" (query), or "a human must do something" (staff-signal). Adding types like `alert` or `escalation` creates semantic overlap. Use priority and labels for further classification.

**staff-signal vs request**: staff-signal always escalates to human channels (by definition, it needs a human). request stays machine-to-machine unless it times out or the receiver marks it needs-human.

## Signal Schema

A signal is a bd bead with type `task` (or `feature` for larger requests), structured metadata, and conventional labels.

### Required Fields

```
Title:       "SIGNAL(<type>): <action description>"
             e.g. "SIGNAL(request): Move renderer to os/web/"
             e.g. "SIGNAL(staff-signal): Sign LLC formation documents"

Labels:      signal, signal:<type>, to:<target-repo>
             e.g. signal, signal:request, to:os

Priority:    0-4 (sender's assessment; receiver may reprioritize)
```

### Metadata (JSON via --metadata)

```json
{
  "signal": {
    "type": "request",
    "from": "3dl",
    "to": ["os"],
    "routing": {
      "agent": "cpeo",
      "tier": "sonnet"
    },
    "context": ["3dl/3dl-644", "docs/architecture.md"],
    "payload": {}
  }
}
```

Field definitions:

| Field | Required | Description |
|-------|----------|-------------|
| `signal.type` | yes | `staff-signal`, `request`, `notify`, `query` |
| `signal.from` | yes | Sender repo name (auto-set by bd signal command) |
| `signal.to` | yes | Target repo name(s), array |
| `signal.routing.agent` | no | Suggested receiving agent/role |
| `signal.routing.tier` | no | Suggested model tier (haiku/sonnet/opus) |
| `signal.context` | no | Array of cross-repo bead refs and file paths |
| `signal.payload` | no | Type-specific structured data (see below) |

### Type-Specific Payloads

**staff-signal**:
```json
{
  "payload": {
    "action_steps": ["Review pages 1-3", "Sign page 4", "File online"],
    "estimated_minutes": 30,
    "artifacts": ["/path/to/doc.pdf"]
  }
}
```

**request**:
```json
{
  "payload": {
    "acceptance": "Renderer produces same HTML output from os/web/ as from 3dl/bin/",
    "deadline": "2026-02-21"
  }
}
```

**notify**:
```json
{
  "payload": {
    "what_changed": "Blog post published to website/blog/vms-journey.html",
    "affected_files": ["blog.html", "blog/vms-journey.html"],
    "source_bead": "3dl/3dl-k9c"
  }
}
```

**query**:
```json
{
  "payload": {
    "question": "Should the API server use bearer token or GitHub OAuth for Phase 1?",
    "options": ["bearer-token", "github-oauth", "both"],
    "decision_authority": "cpeo"
  }
}
```

### Description Convention

The bead description carries the human-readable version of the signal. Metadata carries the machine-readable version. Both must agree.

```
## Signal: request
**From**: 3dl  **To**: os
**Routing**: CPEO (Sonnet)

Move the dashboard renderer from 3dl/bin/render-dashboard to os/web/render.py.
The renderer is an OS service, not org-specific.

**Context**:
- 3dl/3dl-644 (Atom architecture epic)
- /home/baron/projects/os/docs/architecture.md (critical path item #2)

**Acceptance**: Renderer produces identical HTML output from new location.
```

## State Dimensions

Signals use bd's existing `set-state` for lifecycle tracking:

```bash
bd set-state <signal-id> signal=pending    # just created (default)
bd set-state <signal-id> signal=seen       # receiver discovered it
bd set-state <signal-id> signal=acked      # receiver created impl bead
bd set-state <signal-id> signal=resolved   # sender confirmed completion
```

The `signal` dimension tracks the cross-repo handshake. The bead's own `status` tracks the sender's view of completion (open -> closed when resolved).

## Discovery Mechanism

**Decision: bd scans registered repos (Option D from the design brief).**

### Project Registry

Project discovery uses the OS bootstrap system (`os.yml` + `os.conf`). See `docs/bootstrap-config.md`.

```bash
os projects --json       # machine-parseable list of all repos
os sweep                 # cross-project scan for signals + P0/P1
```

The `os sweep` command replaces per-repo `bd config` for project registration. All repos registered via `os bootstrap` are automatically discoverable.

### Inbox Scan

The receiver scans all registered repos for signals addressed to it:

```
For each registered repo R:
  1. Open R's .beads/ database (read-only)
  2. Query: label=to:<my-repo> AND label=signal AND status!=closed
  3. Return matching signals, sorted by priority then created date
```

This is a read-only operation. The receiver never writes to R's database.

### Why Not a Shared Directory?

A shared signals directory (Option B) violates repo sovereignty -- it's a write target outside any repo. A git-based mechanism (Option C) adds latency and complexity for no benefit since all repos are on the same filesystem. Option D is simple, uses bd's existing `--db` flag for cross-repo reads, and requires zero new infrastructure.

### Why Not Push?

Push requires a running daemon or webhook. Pull is simpler: the receiver checks when it cares (session start, periodic sweep). For a solo founder with 5 repos, the scan takes <1 second.

## bd Commands

### `bd signal` -- Create a Signal

```bash
bd signal --to os --type request "Move renderer to os/web/" \
  --context 3dl/3dl-644 \
  --route cpeo:sonnet \
  --priority 1

# Equivalent to:
bd create "SIGNAL(request): Move renderer to os/web/" \
  -p 1 \
  -l signal,signal:request,to:os \
  --metadata '{"signal":{"type":"request","from":"3dl","to":["os"],"routing":{"agent":"cpeo","tier":"sonnet"},"context":["3dl/3dl-644"],"payload":{}}}'
```

The `bd signal` command is a convenience wrapper. Signals are just beads.

**Flags**:
- `--to <repo>[,<repo>...]` (required) -- target repo(s)
- `--type <signal-type>` (required) -- staff-signal, request, notify, query
- `--context <ref>[,<ref>...]` -- cross-repo bead refs or file paths
- `--route <agent>[:<tier>]` -- suggested agent and model tier
- `-p <priority>` -- standard bd priority

### `bd inbox` -- Check Incoming Signals

```bash
bd inbox                    # signals addressed to this repo
bd inbox --from 3dl         # only signals from 3dl
bd inbox --type request     # only requests
bd inbox --priority 0-1     # only P0/P1
bd inbox --json             # machine-parseable
```

Scans all registered repos for beads with `label=to:<this-repo> AND label=signal AND status!=closed`.

Output:
```
FROM     ID            P  TYPE     TITLE
3dl      3dl-xyz       1  request  Move renderer to os/web/
3dl      3dl-abc       2  notify   Blog post published
website  website-123   0  query    Auth model for API server?
```

### `bd ack` -- Acknowledge a Signal

```bash
bd ack 3dl/3dl-xyz --with os-456
```

This does two things:
1. In the local repo: adds comment to os-456: `Acknowledging signal 3dl/3dl-xyz`
2. In the local repo: adds label `ack:3dl/3dl-xyz` to os-456

The sender's signal bead is NOT modified (repo sovereignty). The sender discovers the ack during their next scan by checking if any repo has beads labeled `ack:<my-repo>/<signal-id>`.

**Alternative**: If the sender wants to track ack state, they run:
```bash
bd set-state <signal-id> signal=acked --reason "Acked by os as os-456"
```
This is a sender-side operation, done manually or by a sweep script.

### `bd resolve` -- Mark Signal Complete

```bash
bd resolve 3dl-xyz --reason "os-456 closed, renderer moved"
```

Equivalent to:
```bash
bd set-state 3dl-xyz signal=resolved --reason "os-456 closed, renderer moved"
bd close 3dl-xyz --reason "Resolved: os-456 closed, renderer moved"
```

Only the sender runs this (it's their bead). Triggered when the receiver notifies completion, or when the sender's sweep detects the linked impl bead is closed.

### `bd sweep` -- Cross-Project Scan (Generalized CEO Sweep)

```bash
bd sweep                   # all repos: signals + P0/P1 + stale
bd sweep --signals-only    # just pending signals for this repo
bd sweep --all-repos       # scan everything, not just inbox
bd sweep --json            # machine-parseable
```

This generalizes the current CEO sweep script into a bd command. It:
1. Scans all registered repos
2. Finds signals addressed to this repo (inbox)
3. Finds P0/P1 open beads across all repos (awareness)
4. Checks for signals this repo sent that were acked/resolved (outbox status)
5. Reports stale signals (created >48h ago, still pending)

## Lifecycle

```
SENDER REPO                          RECEIVER REPO
-----------                          -------------

1. bd signal --to <recv> ...
   Creates signal bead
   Labels: signal, signal:<type>,
           to:<recv>
   State: signal=pending
                                     2. bd inbox (or bd sweep)
                                        Discovers signal
                                        (read-only scan of sender's .beads/)

                                     3. bd create "Impl: <action>"
                                        Creates local impl bead
                                        Description refs sender signal

                                     4. bd ack <sender>/<signal-id> --with <impl-id>
                                        Links impl bead to signal
                                        (local labels + comment only)

5. bd sweep (or manual check)
   Discovers ack
   bd set-state <signal> signal=acked
                                     6. Work happens on impl bead
                                        Normal bd workflow

                                     7. bd close <impl-id> --reason "Done"

                                     8. bd signal --to <sender> --type notify
                                        "Completed: <action>"
                                        Context refs: original signal + impl bead

9. bd sweep
   Discovers notify
   bd resolve <signal-id>
   Signal bead closed
```

### ASCII Lifecycle Diagram

```
Sender                              Receiver
  |                                    |
  |-- signal bead created ------------>|
  |   (signal=pending)                 |
  |                                    |
  |                          inbox ----|
  |                     (discovers)    |
  |                                    |
  |                   impl bead -------|
  |                     created        |
  |                                    |
  |<---------- ack (label+comment) ----|
  |   (signal=acked)                   |
  |                                    |
  |                       ... work ... |
  |                                    |
  |<--------- notify signal -----------|
  |   (signal=resolved)               |
  |   signal bead closed              |
  |                                    |
```

### Simplified Flow (Notify)

Notify signals are fire-and-forget. No ack/resolve cycle needed.

```
Sender                              Receiver
  |                                    |
  |-- notify signal ------------------->|
  |   (signal=pending)                 |
  |                                    |
  |                          inbox ----|
  |                     (reads it)     |
  |                                    |
  |                   acts (or not) ---|
  |                                    |
  |   (auto-resolve after 7 days      |
  |    or receiver marks seen)         |
```

## Escalation Rules

When does a channel-4 signal cross into channels 1-3?

### Always Escalate

| Condition | Target Channel | Action |
|-----------|---------------|--------|
| `staff-signal` type | Teams (#staff-queue) + Web (dashboard) | By definition, staff-signals need humans |
| Signal marked `needs-human` | Teams (#alerts) + Web | Sender explicitly flagged it |
| P0 signal, any type | Teams (#alerts) | Urgency demands attention |

### Conditional Escalate

| Condition | Target Channel | Trigger |
|-----------|---------------|---------|
| Request, no ack after 48h | Teams (#alerts) | Stale signal sweep |
| Query, decision authority = founder | Teams (#command) + Web | Agent can't decide |
| Request, P1, no ack after 24h | Teams (#alerts) | Priority-adjusted timeout |

### Never Escalate

| Condition | Reason |
|-----------|--------|
| Notify, any priority | FYI only, no action needed |
| Request, acked and in-progress | Being handled, no human needed |
| Query, decision authority = agent | Agent can answer without human |

### Escalation Mechanics

The `bd sweep` command checks escalation conditions. When triggered:
1. Creates a bead in the org repo (3dl) with label `escalated` + reference to the signal
2. Posts to the appropriate Teams channel (via Teams bot API)
3. Adds the signal to the web dashboard's attention queue

The escalation is idempotent -- running sweep twice doesn't create duplicate escalations. The `bd kv` store tracks which signals have been escalated:

```bash
bd kv set "escalated:<repo>/<signal-id>" "2026-02-14T17:00:00Z"
```

## Cross-Reference Linking

### Format

```
<repo-name>/<bead-id>
```

Examples: `3dl/3dl-644`, `os/os-abc`, `galtrader/galtrader-d0a`

This convention is already established. Signals formalize it.

### How Links Work

- **Sender's signal bead**: description and metadata contain `context` refs pointing to relevant beads in any repo
- **Receiver's impl bead**: description contains `Ref: <sender>/<signal-id>` (human-readable) and label `ack:<sender>/<signal-id>` (machine-queryable)
- **Neither modifies the other's beads**

### Resolving Cross-References

Cross-refs are resolved at read time:
```bash
# From any repo, read a cross-referenced bead:
bd show <bead-id> --db /home/baron/projects/<repo>/.beads/*.db --no-daemon
```

The API layer (`GET /beads/:id`) resolves cross-refs automatically by detecting the `<repo>/<bead-id>` pattern and fetching from the appropriate database.

## Volume Management

### Priority Filtering

`bd inbox` and `bd sweep` support `--priority` to filter noise:
- CEO sweep: `--priority 0-1` by default
- Agent inbox: all priorities (agents handle their own triage)

### Batching

Low-priority signals (P3-P4) are batched:
- `bd sweep` reports them as a count, not individual items: "5 low-priority signals from galtrader"
- Detailed view on request: `bd inbox --from galtrader --priority 3-4`

### Deduplication

Before creating a signal, check for an existing open signal with the same `to`, `type`, and similar title:

```bash
bd query "label=signal AND label=to:os AND label=signal:request AND status!=closed AND title=renderer" --no-daemon
```

If a match exists, add a comment to the existing signal instead of creating a duplicate.

### Auto-Resolve Stale Signals

Notify signals auto-resolve (close) after 7 days if not explicitly resolved. The `bd sweep` command handles this:
```bash
# Close stale notify signals
bd query "label=signal:notify AND status!=closed AND created>7d" --no-daemon
# For each: bd close <id> --reason "Auto-resolved: notify signal aged out"
```

## Relation to Existing Primitives

### Gates

Signals can create gates when cross-repo synchronization is needed:

```bash
# Sender creates signal with a gate
bd signal --to os --type request "Move renderer" -p 1
# Then blocks downstream work on the signal:
bd dep add <downstream-bead> <signal-id>
```

The sender's downstream bead is blocked until the signal is resolved. The `bd gate` bead type (with `await_id` format `<rig>:<bead-id>`) is the existing mechanism for cross-rig waits -- signals build on this.

### Comments

Signal beads use comments for the conversation thread:
- Sender adds context: `bd comments add <signal-id> "Updated acceptance criteria: ..."`
- After ack discovery, sender notes: `bd comments add <signal-id> "[SIGNAL] Acked by os as os-456"`
- Resolution reason goes in the close: `bd close <signal-id> --reason "Resolved: ..."`

### Dependencies

Signal beads can be wired into dependency trees like any bead:
```bash
bd dep add <impl-bead> <some-other-bead>   # normal deps
bd dep add <downstream> <signal-id>         # block on signal resolution
```

### Labels

Signal labels follow a namespace convention:

| Label | Meaning |
|-------|---------|
| `signal` | This bead is a signal |
| `signal:<type>` | Signal type (staff-signal, request, notify, query) |
| `to:<repo>` | Target repo |
| `ack:<repo>/<bead-id>` | This bead acknowledges a signal |
| `escalated` | Signal has been escalated to human channels |

### State Dimensions

The `signal` dimension tracks cross-repo handshake state (pending, seen, acked, resolved). This is orthogonal to the bead's own `status` dimension.

## Implementation Tasks

Ordered by dependency. Each becomes a bead.

### Phase 1: Convention Only (No Code)

1. **Define signal label conventions** -- Document the label namespaces (`signal`, `signal:<type>`, `to:<repo>`, `ack:<ref>`). Add to each project's CLAUDE.md. No code changes.

2. **Configure signal.repos in all project repos** -- Run `bd config set` in each repo to register the project registry. Validate with `bd config list`.

3. **Migrate existing STAFF-SIGNAL beads** -- Re-label existing `STAFF-SIGNAL:` beads with the new convention (`signal`, `signal:staff-signal`, `to:3dl`). Add metadata.

4. **Update cross-project-protocol.md** -- Replace the current STAFF-SIGNAL section with the generalized signal protocol reference. Keep the CEO sweep section but note it is being replaced by `bd sweep`.

### Phase 2: bd Commands (CLI)

5. **`bd signal` command** -- Convenience wrapper for creating signal beads. Validates `--to` against configured repos. Sets labels and metadata. Calls `bd create` internally.

6. **`bd inbox` command** -- Cross-repo scan for signals addressed to this repo. Uses `--db` flag to read other repos' databases. Read-only. Supports `--from`, `--type`, `--priority`, `--json` filters.

7. **`bd ack` command** -- Links a local bead to a cross-repo signal. Adds label `ack:<ref>` and comment. Local-only writes.

8. **`bd resolve` command** -- Sets signal state to resolved and closes the bead. Sender-side only.

9. **`bd sweep` command** -- Generalized cross-project scan. Replaces the Python CEO sweep script. Supports `--signals-only`, `--all-repos`, `--json`. Checks escalation conditions. Reports stale signals.

### Phase 3: Escalation + Surface Integration

10. **Escalation engine in `bd sweep`** -- Check escalation conditions (timeout, priority, needs-human). Track escalated signals in kv store. Output escalation actions for surface layers to consume.

11. **API endpoints for signals** -- `GET /signals/inbox`, `GET /signals/outbox`, `POST /signals`, `POST /signals/:id/ack`, `POST /signals/:id/resolve`. Thin wrappers around the bd commands.

12. **Teams integration** -- `bd sweep` output feeds Teams notifications. Staff-signals auto-post to #staff-queue. Escalated signals post to #alerts.

13. **Web dashboard integration** -- Signals inbox/outbox as a dashboard section. Pending signals with counts. Escalated signals highlighted.

### Phase 4: Automation

14. **Auto-resolve stale notify signals** -- `bd sweep` closes notify signals older than 7 days.

15. **Auto-ack detection** -- `bd sweep` detects when a receiver has created a bead with `ack:<signal-ref>` label and updates the sender's signal state.

16. **Scheduled sweep via GitHub Actions** -- Run `bd sweep --json` on a cron, post results to Teams webhook, push stale signal warnings.
