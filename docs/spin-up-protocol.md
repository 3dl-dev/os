# Spin-Up Protocol

> **When to use this:** A user is in the OS repo and describes a new project they want to create. Follow this protocol to go from conversation to a fully scaffolded, committed, pushed project — then hand them off to the new project directory.

## Phase 1: Conversational Intake

Listen to what the user describes. Extract these essentials:

| Field | Required | Example |
|-------|----------|---------|
| Project name | Yes | `aerocloak` |
| One-liner | Yes | "Radar-absorbing ventilation system for stealth aircraft" |
| Domain | Yes | hardware / SaaS / data pipeline / content / research / other |
| Agents (beyond PM) | Yes | Hardware Engineer, Tech Comms, Designer |
| Key work types | Yes | needed for model mapping |
| Directory path | No | defaults to `~/projects/<name>` |

### Adaptive Depth

- **Rich description** (user gave name, domain, and detailed scope): confirm your understanding, ask only about gaps — likely just agent roster and model mapping.
- **Thin description** (user said "I want to start a new project"): walk through each field above, one at a time.
- **Middle ground**: ask follow-ups only for what's missing.

### Agent Suggestions

Offer domain-based defaults (same as BOOTSTRAP.md Section 2):

| Domain | Typical Agents |
|--------|---------------|
| Hardware | Hardware Engineer, Tech Comms, Designer, Build Coach |
| SaaS | Backend Engineer, Frontend Engineer, DevOps, QA, Technical Writer |
| Research | Researcher, Data Analyst, Technical Writer |
| Content | Writer, Editor, Designer |
| Data pipeline | Data Engineer, DevOps, QA |

For each agent, get a one-sentence role description.

### Model Mapping

Propose a first-pass mapping based on the work types and let the user adjust:

- **Opus**: Novel design, architecture, cross-domain synthesis
- **Sonnet**: Structured analysis, specs, implementation
- **Haiku**: Mechanical updates, templates, config

### Confirm Before Proceeding

Summarize what you heard back to the user:

```
Project: <name>
One-liner: <description>
Domain: <domain>
Agents: <list with roles>
Model mapping: <table>
Path: ~/projects/<name>
```

Wait for explicit go-ahead before entering Phase 2.

---

## Phase 2: Mechanical Execution

Run these steps in order. Each step must succeed before the next.

### Step 0: Create OS Bead

Before touching any files, create a bead in the OS repo to track this spin-up:

```bash
bd create "Spin-up: <project-name>" -p 1 --description="Conversational spin-up for <name>. <one-liner>"
bd update <id> --status in_progress --claim
```

Close this bead at the end of Step 11 with a summary of what was set up.

### Step 1: Scaffold

```bash
new-project ~/projects/<name>
```

If the directory already exists, stop and ask the user what to do (rename, delete existing, or abort).

### Step 2: Fill CLAUDE.md

Edit `~/projects/<name>/CLAUDE.md` — replace placeholders from the conversation:

| Placeholder | Source |
|-------------|--------|
| `[PROJECT NAME]` (both in comment and heading) | Project name |
| `[One-line description of what this project is.]` | One-liner |
| `[Agent Name]` rows in Agent Roster table | Each agent from conversation |
| `docs/agent-[name].md` in Spec column | Matching agent spec path |
| `[service name]` in Container column | `(none yet)` unless discussed |
| `[Role description]` in Role column | Agent role from conversation |
| `[Task type] → [Agent Name]` routing rules | One per agent |
| Model mapping `[brackets]` | Work types and model assignments |

**Leave these sections with placeholders** (they'll be handled during in-project bootstrap):
- Design Change Cascade (Sections 5)
- Source of Truth Hierarchy (Section 6)
- Artifact Conventions (Section 7)
- Repo Structure (will need project-specific paths)

The bootstrap comment at the top of CLAUDE.md stays — it signals to the in-project session that bootstrap isn't fully complete.

### Step 3: Create Agent Specs

For each agent identified in the conversation, copy `docs/agent-TEMPLATE.md` to `docs/agent-<name>.md` in the new project directory. Fill in:
- Agent name and role
- Primary/secondary responsibilities (from conversation context)
- Routing rule
- Leave tool requirements and output standards as TODOs

### Step 4: Fill Product Vision

Edit `~/projects/<name>/docs/product-vision.md`:
- Replace `[What this project does, in one sentence.]` with the one-liner

### Step 5: Mark Completed Sections in BOOTSTRAP.md

For each section handled during spin-up, add `<!-- COMPLETED-IN-SPINUP -->` immediately after the section heading:

```markdown
## Section 1: Project Identity
<!-- COMPLETED-IN-SPINUP -->
```

Sections typically completed during spin-up: **1 (Project Identity), 2 (Agent Roster), 3 (Model Mapping)**.

Sections left for in-project bootstrap: **4-9** (Container Services, Design Change Cascade, Source of Truth, Artifact Conventions, Website, Devblog).

### Step 6: Initial Commit

From `~/projects/<name>`:

```bash
git add -A
git commit -m "Bootstrap: project identity, agents, and model mapping"
```

### Step 7: Create GitHub Repo

```bash
cd ~/projects/<name>
gh repo create <name> --private --source=. --push
```

If `gh` auth isn't configured, tell the user to run `gh auth login` and retry. Don't try to work around auth issues.

### Step 8: Initialize Beads

```bash
cd ~/projects/<name>
bd init --prefix <name>
```

### Step 9: Create and Close Bootstrap Bead

```bash
bd create "Spin-up: project identity, agents, model mapping" -p 0
bd close <bead-id> -m "Configured via OS spin-up protocol. Sections 1-3 complete. Sections 4-9 remain for in-project bootstrap."
```

### Step 10: Final Commit and Push

```bash
git add -A
git commit -m "Spin-up complete: beads initialized, bootstrap bead closed"
git push
```

### Step 11: Close OS Bead and Hand Off

Close the OS repo bead from Step 0:

```bash
bd close <os-bead-id> --reason "Spun up <name>: <sections completed>. Remaining sections for in-project bootstrap."
bd sync
```

Tell the user:

```
Project scaffolded and pushed to GitHub.

Sections completed:
- Project identity
- Agent roster
- Model mapping

Remaining (Claude will pick these up in the project):
- Container services
- Design change cascade
- Source of truth hierarchy
- Artifact conventions
- Website
- Devblog

Next:
  cd ~/projects/<name> && claude
```

---

## Edge Cases

| Situation | Action |
|-----------|--------|
| Directory already exists | Ask user: rename new project, remove existing dir, or abort |
| `gh` not authenticated | Tell user to run `gh auth login` first, then retry from Step 7 |
| User wants non-default path | Use their specified path instead of `~/projects/<name>` |
| User wants public repo | Use `gh repo create <name> --public --source=. --push` |
| `bd` not available | Tell user to run `setup.sh` from the OS repo first |
| User changes mind mid-conversation | Go back to Phase 1 and re-confirm |
| User wants to skip GitHub repo | Skip Steps 7 and 10 (push), note that they can do it later |

---

## What This Protocol Covers vs. What It Doesn't

**Covered in spin-up** (BOOTSTRAP.md Sections 1-3):
- Project name, description, domain
- Agent roster and routing rules
- Task-type to model mapping

**Left for in-project bootstrap** (BOOTSTRAP.md Sections 4-9):
- Container services — needs hands-on exploration of project tooling
- Design change cascade — needs the user working in the project context
- Source of truth hierarchy — project-specific, best decided once work begins
- Artifact conventions — depends on what the project actually produces
- Website — separate decision with its own implications
- Devblog — quick yes/no but part of the in-project flow

This split exists because Sections 1-3 can be answered from a high-level project description, while Sections 4-9 need the user to be thinking in the project context.
