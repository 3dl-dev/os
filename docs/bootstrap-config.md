# OS Bootstrap & Configuration Architecture

**Status**: Spec
**Bead**: 3dl-h8c
**Date**: 2026-02-15

## Problem

The three-layer model (OS / Organization / Project) is documented in `docs/architecture.md`, but the connections between layers are ad-hoc:

- Project registry is a hardcoded table in `~/.claude/CLAUDE.md`
- Dashboard config is a hand-maintained YAML in `os/web/dashboard-config.yml`
- `new-project.sh` doesn't register the project anywhere
- No formal org declaration — 3DL is implicit
- Cross-project protocol assumes paths that aren't discoverable

Each new piece of tooling (dashboard renderer, Teams bot, API server, CEO sweep) reinvents project discovery. The bootstrap/config layer makes this discoverable and consistent.

## Design: `os.yml`

A single config file per organization that declares:
- The org's identity
- Its projects and their locations
- Config references consumed by OS services

### Where It Lives

In the **organization repo root**: `3dl/os.yml`, `some-other-org/os.yml`.

The OS repo itself does NOT have an os.yml — it's the kernel, not an org. The OS discovers orgs by scanning known paths.

### Format

```yaml
# 3dl/os.yml — Third Division Labs organization config

org:
  name: 3dl
  display: Third Division Labs
  bead-prefix: 3dl

projects:
  os:
    path: ~/projects/os
    bead-prefix: os
    role: platform        # Special: this is the OS itself
  website:
    path: ~/projects/website
    bead-prefix: website
  mag-shield:
    path: ~/projects/mag-shield
    bead-prefix: mag-shield
  galtrader:
    path: ~/projects/galtrader
    bead-prefix: galtrader
  vms:
    path: ~/projects/vms
    bead-prefix: vms

dashboard:
  repo: ~/projects/dashboard
  # Standalone docs to surface in review queue (paths relative to org repo)
  standalone-reviews:
    - path: docs/templates/msa.md
      action: Review MSA template with Counsel
      agent: counsel
    - path: docs/templates/nda.md
      action: Review NDA template with Counsel
      agent: counsel
    - path: docs/templates/sow.md
      action: Review SOW template with Counsel
      agent: counsel
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| `org.name` | Yes | Short identifier (used in cross-refs, bead prefixes) |
| `org.display` | No | Human-readable name (defaults to `org.name`) |
| `org.bead-prefix` | Yes | Prefix for beads in the org repo |
| `projects.<name>.path` | Yes | Filesystem path (supports `~` expansion) |
| `projects.<name>.bead-prefix` | Yes | Expected bead prefix in that project |
| `projects.<name>.role` | No | `platform` = OS layer. Default = workload project |
| `dashboard.repo` | No | Where to write dashboard output |
| `dashboard.standalone-reviews` | No | Docs to surface without bead refs |

### Path Resolution

Paths in os.yml support:
- `~/projects/foo` — tilde expansion (resolved at parse time)
- Relative paths — relative to the os.yml file's directory
- Absolute paths — used as-is

Future (not v1): `github:owner/repo` for repos not on the local filesystem. This would require `gh repo clone` during bootstrap.

## Discovery: How the OS Finds Orgs

### `os.conf` — Machine-Level Registry

Lives at `~/.local/share/os/os.conf`. Maps org names to their repo paths.

```
# ~/.local/share/os/os.conf
# One org per line: name path
3dl /home/baron/projects/3dl
```

Created by `os bootstrap`. Read by all OS tools. This is the **only** machine-level state the OS maintains (beyond symlinks created by `setup.sh`).

### Resolution Order

When an OS tool needs to find orgs/projects:

1. Read `~/.local/share/os/os.conf` → list of org repos
2. For each org repo, read `os.yml` → org config + project list
3. Resolve all paths → validate existence

This two-step indirection means:
- `os.conf` is tiny (one line per org) and machine-specific
- `os.yml` is rich and git-tracked (shared across machines via the org repo)
- Adding a new org = one line in os.conf + os.yml in the org repo

## Bootstrap Command: `os bootstrap`

A new `bin/os` script that handles bootstrap and other OS-level operations.

### `os bootstrap <org-repo-path>`

Registers an org and validates its projects.

```bash
$ os bootstrap ~/projects/3dl

Reading os.yml from /home/baron/projects/3dl...
Org: 3dl (Third Division Labs)
Projects:
  os          ~/projects/os          ✓ exists
  website     ~/projects/website     ✓ exists
  mag-shield  ~/projects/mag-shield  ✓ exists
  galtrader   ~/projects/galtrader   ✓ exists
  vms         ~/projects/vms         ✓ exists

Registered 3dl in ~/.local/share/os/os.conf
Generated dashboard config at ~/projects/os/web/dashboard-config.yml

Done. The OS now knows about 3dl and its 5 projects.
```

What it does:
1. Parse `os.yml` from the given path
2. Validate all project paths exist (warn on missing, don't fail)
3. Add/update the org in `~/.local/share/os/os.conf`
4. Generate derived configs (dashboard-config.yml)

### `os status`

Show what the OS knows.

```bash
$ os status

OS: /home/baron/projects/os (v1)
Orgs: 1

3dl (Third Division Labs)
  Config: /home/baron/projects/3dl/os.yml
  Projects: 5 (5 exist, 0 missing)
    os          ~/projects/os          v1 (aligned)
    website     ~/projects/website     v0 (outdated)
    mag-shield  ~/projects/mag-shield  v0 (outdated)
    galtrader   ~/projects/galtrader   v0 (outdated)
    vms         ~/projects/vms         v0 (outdated)
```

Combines os.conf, os.yml, and os-check output.

### `os projects [--json]`

List all projects across all orgs. Used by tools that need project discovery.

```bash
$ os projects --json
[
  {"org": "3dl", "name": "os", "path": "/home/baron/projects/os", "prefix": "os"},
  {"org": "3dl", "name": "website", "path": "/home/baron/projects/website", "prefix": "website"},
  ...
]
```

This replaces hardcoded project lists in dashboard-config.yml, CLAUDE.md tables, etc.

## Derived Configs

`os bootstrap` generates configs consumed by OS services. These are **derived** from os.yml — not hand-edited.

### Dashboard Config

Generated at `os/web/dashboard-config.yml`. The renderer reads this at render time.

```yaml
# AUTO-GENERATED by os bootstrap — do not edit manually
# Source: /home/baron/projects/3dl/os.yml

projects:
  3dl: /home/baron/projects/3dl
  os: /home/baron/projects/os
  website: /home/baron/projects/website
  mag-shield: /home/baron/projects/mag-shield
  galtrader: /home/baron/projects/galtrader
  vms: /home/baron/projects/vms

dashboard_repo: /home/baron/projects/dashboard
org_repo: 3dl

standalone_review_docs:
  - path: docs/templates/msa.md
    action: Review MSA template with Counsel
    agent: counsel
  - path: docs/templates/nda.md
    action: Review NDA template with Counsel
    agent: counsel
  - path: docs/templates/sow.md
    action: Review SOW template with Counsel
    agent: counsel
```

### Project Registry (CLAUDE.md)

The project registry table in `~/.claude/CLAUDE.md` is currently hand-maintained. After bootstrap exists, the PM agent should generate it from `os projects --json` rather than editing it manually.

## Nesting: Project-as-Org

A project can declare itself as an org by including its own `os.yml`. This enables:
- A game project that has sub-projects (engine, assets, server)
- A consulting engagement with multiple workstreams
- Testing the OS on the OS itself

```yaml
# galtrader/os.yml — GalTrader as a sub-org

org:
  name: galtrader
  display: GalTrader
  bead-prefix: galtrader
  parent: 3dl              # Optional: declares this is a sub-org

projects:
  engine:
    path: ./engine          # Relative to os.yml location
    bead-prefix: gt-engine
  server:
    path: ./server
    bead-prefix: gt-server
```

`os bootstrap` handles nesting by:
1. Registering the parent org first
2. Discovering nested os.yml files in project paths
3. Registering nested orgs with a `parent` reference

Not v1 — document the design, implement when a real use case appears.

## Integration Points

### render-dashboard

Currently reads `dashboard-config.yml`. After bootstrap:
- Config is auto-generated by `os bootstrap`
- Renderer can also call `os projects --json` directly for project discovery
- No manual config maintenance

### Teams Bot

Currently has project paths hardcoded. After bootstrap:
- Bot reads `os.conf` → org repos → os.yml at startup
- Project commands (`/atom projects`, `/atom show mag-shield/ms-123`) resolve via os.yml

### API Server

Currently uses config file for project paths. After bootstrap:
- API reads the same os.conf → os.yml chain
- `/projects` endpoint returns `os projects --json` output
- Cross-project reads use discovered paths

### new-project.sh

Currently creates a project without registering it. After bootstrap:
- `new-project` stamps `.os-version` (already done)
- User runs `os bootstrap` to pick up the new project (or `new-project` calls it)
- Project appears in dashboard, Teams, API automatically

### Cross-Project Protocol

Currently relies on hardcoded project registry in CLAUDE.md. After bootstrap:
- CEO sweep uses `os projects --json` to discover spoke repos
- Signal protocol resolves `<repo>/<bead-id>` via os.yml paths
- No manual registry maintenance

## Implementation Plan

### Phase 1: os.yml + os bootstrap (this bead)

1. Define os.yml format (this spec)
2. Create `3dl/os.yml` in the 3dl repo
3. Build `bin/os` script with `bootstrap` and `status` subcommands
4. Generate dashboard-config.yml from os.yml
5. Create `~/.local/share/os/os.conf` during bootstrap

### Phase 2: Tool Integration

1. Update render-dashboard to use generated config (or call `os projects`)
2. Update API server to discover projects via os.conf
3. Update new-project.sh to register in os.yml
4. Generate CLAUDE.md project registry table from os.yml

### Phase 3: Nesting + Remote (future)

1. Support nested os.yml (project-as-org)
2. Support `github:owner/repo` path syntax
3. Cross-machine federation (multiple os.conf sources)

## Non-Goals

- **Multi-tenant**: Each machine has one os.conf. No shared registries.
- **Hot reload**: Tools read config at startup. Changes require restart (or `os bootstrap` re-run).
- **Schema validation**: Minimal — check required fields, warn on unknown keys. Don't build a validator.
- **Migration tooling**: Existing projects without os.yml continue to work. Bootstrap is opt-in.
