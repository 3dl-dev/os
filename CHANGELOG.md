# OS Changelog

All notable changes to the OS repo that affect downstream projects.

Each entry notes which files changed and whether existing projects need manual updates.

## Version 1 (2026-02-15)

Initial versioned release. Establishes the baseline for compliance checking.

- **Added**: `VERSION` file, `CHANGELOG.md`, `bin/os-check` compliance script
- **Added**: `.os-version` stamp in project template
- **Changed**: `new-project.sh` now stamps OS version into new projects
- **Backport**: None required — existing projects get version 0 (pre-versioning)

### Components at v1

- `claude/CLAUDE.md` — user-level instructions (session protocol, beads workflow, model routing, blog pipeline, rules)
- `docker/` — shared Dockerfiles + compose for `bd` and `gh`
- `bin/` — wrappers: `bd`, `gh`, `render-dashboard`, `atom-api`, `atom-bot`
- `template/` — project skeleton (CLAUDE.md, BOOTSTRAP.md, agent specs, blog dirs)
- `setup.sh` — machine bootstrap
- `new-project.sh` — project scaffolding
