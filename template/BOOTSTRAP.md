# Bootstrap Checklist

Work through these questions to configure this project. Each answer fills in a section of `CLAUDE.md` or creates a file in `docs/`.

When you start your first Claude Code session in this repo, you can walk through this checklist together — or fill it in yourself and let the PM agent pick it up.

---

## 1. Project Identity

> Fills in: CLAUDE.md header

- **Name**: What's the project called?
- **One-liner**: What does it do, in one sentence?
- **Domain**: Hardware / SaaS / data pipeline / content / research / other?

## 2. Agent Roster

> Fills in: CLAUDE.md Agent Roster table + creates `docs/agent-*.md` specs

What specialized agents does this project need? Use `docs/agent-TEMPLATE.md` as a starting point for each.

Common patterns:
- **Hardware project**: Hardware Engineer, Tech Comms, Designer, Build Coach
- **SaaS product**: Backend Engineer, Frontend Engineer, DevOps, QA, Technical Writer
- **Research project**: Researcher, Data Analyst, Technical Writer
- **Content project**: Writer, Editor, Designer

For each agent, define: role, tools needed, output standards, interaction with PM.

## 3. Container Services

> Fills in: `docker-compose.yml` + `Dockerfile.*` + `bin/*`

What project-specific tools need containerizing? Shared tools (`bd`, `gh`) are already available via the OS repo.

Examples:
- Python with numpy/scipy (engineering calcs)
- Node with Mermaid + Pandoc (diagram/doc rendering)
- Rust toolchain (firmware)
- PostgreSQL (local database)

For each: create a Dockerfile, add a service to `docker-compose.yml`, add a thin wrapper in `bin/`.

## 4. Design Change Cascade

> Fills in: CLAUDE.md Design Change Cascade section

When the architecture or key specs change, what downstream reviews must happen?

Hardware example:
```
Design Change → HW Review → Legal Review → BOM Update → Report Regen → Website Check
```

SaaS example:
```
Architecture Change → Security Review → Migration Plan → API Docs Update → Changelog
```

Define: the specific downstream beads, their priorities, dependencies, which agent handles each, and what each produces.

## 5. Source of Truth Hierarchy

> Fills in: CLAUDE.md Source of Truth Hierarchy section

When artifacts disagree, which one wins?

Hardware example:
```
Product vision → Engineering calculations → Specifications → Report
```

SaaS example:
```
Product requirements → API contracts → Implementation → Documentation
```

## 6. Artifact Types

> Fills in: CLAUDE.md Artifact Conventions section

What kinds of artifacts will this project produce?

Common types:
- Specifications (markdown in `docs/`)
- Calculations / analysis scripts (Python in `calcs/`)
- Diagrams (Mermaid in `docs/diagrams/`, rendered to `docs/img/`)
- Test suites
- Data pipelines
- API documentation

## 7. Website

> Fills in: Designer agent scope, `site/` directory

Does this project need a website? If yes:
- What's the audience? (investors, users, technical reviewers, general public)
- Static site or app? (default: static HTML/CSS in `site/`, deployed via GitHub Pages)
- Visual identity: will be defined with the Designer agent in an early session

## 8. Devblog

> Already configured via OS-level CLAUDE.md. This step is confirmation.

The blog pipeline (candidate accumulation → outline → voiced draft → editorial → publish) is active by default. The PM agent will flag blog-worthy moments during normal work.

- **Voice profile**: `docs/agent-blog.md` carries your voice across projects. Review it — adjust if this project has a different public voice.
- **Opt out**: If this project doesn't need a blog, remove the `docs/blog/` directory and note "No devblog" in CLAUDE.md.

---

## When You're Done

1. Fill in all `[BRACKETED PLACEHOLDERS]` in `CLAUDE.md`
2. Create agent specs in `docs/agent-*.md` (one per agent from step 2)
3. Create any Dockerfiles and bin wrappers from step 3
4. Delete this file (or keep it as a record of your bootstrap decisions)
5. Commit: `git add -A && git commit -m "Bootstrap: configure project"`
