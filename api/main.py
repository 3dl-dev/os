"""Atom API — thin REST wrapper around bd (beads CLI).

Single-file FastAPI server. Every endpoint shells out to `bd` and returns JSON.
Auth: static bearer token from ATOM_API_TOKEN env var.
Config: projects.yml in the same directory lists registered projects.
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml
from fastapi import Depends, FastAPI, HTTPException, Header, Query, Request
from fastapi.responses import JSONResponse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_DIR = Path(__file__).resolve().parent
PROJECTS_BASE = Path(os.environ.get("PROJECTS_BASE", "/home/baron/projects"))
BD = os.environ.get("BD_PATH", "bd")
API_TOKEN = os.environ.get("ATOM_API_TOKEN", "")
LISTEN_PORT = int(os.environ.get("ATOM_API_PORT", "3131"))

# Load project registry
_projects_file = API_DIR / "projects.yml"
if _projects_file.exists():
    with open(_projects_file) as f:
        _cfg = yaml.safe_load(f) or {}
else:
    _cfg = {}

PROJECTS: dict[str, dict] = {}
for name, info in (_cfg.get("projects") or {}).items():
    project_path = PROJECTS_BASE / name
    PROJECTS[name] = {
        "path": str(project_path),
        "prefix": info.get("prefix", name),
    }

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_bd(args: list[str], cwd: str | None = None) -> dict | list | str:
    """Run a bd command and return parsed JSON (or raw text on failure)."""
    cmd = [BD, "--no-daemon", "--no-db"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=30,
        )
    except FileNotFoundError:
        raise HTTPException(502, detail="bd binary not found")
    except subprocess.TimeoutExpired:
        raise HTTPException(504, detail="bd command timed out")

    if result.returncode != 0:
        stderr = result.stderr.strip()
        # bd returns 1 for "not found" — map to 404
        if "not found" in stderr.lower() or "no issue" in stderr.lower():
            raise HTTPException(404, detail=stderr or "not found")
        raise HTTPException(502, detail=stderr or f"bd exited {result.returncode}")

    stdout = result.stdout.strip()
    if not stdout:
        return {}

    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        # Some bd commands return plain text even with --json
        return {"output": stdout}


def _project_cwd(project: str | None) -> str:
    """Resolve a project name to its working directory."""
    if project is None:
        # Default to the OS repo itself
        return str(PROJECTS_BASE / "os")
    if project not in PROJECTS:
        raise HTTPException(404, detail=f"unknown project: {project}")
    path = PROJECTS[project]["path"]
    if not Path(path).is_dir():
        raise HTTPException(404, detail=f"project directory not found: {path}")
    return path


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

async def require_auth(authorization: Optional[str] = Header(None)):
    """Validate bearer token. Skipped when ATOM_API_TOKEN is unset (dev mode)."""
    if not API_TOKEN:
        return  # No auth required in dev mode
    if not authorization:
        raise HTTPException(401, detail="missing Authorization header")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or token != API_TOKEN:
        raise HTTPException(401, detail="invalid token")


async def require_write_auth(authorization: Optional[str] = Header(None)):
    """Write endpoints always require auth (even if token is unset, warn)."""
    if not API_TOKEN:
        return  # Dev mode — allow writes without auth
    await require_auth(authorization)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Atom API",
    version="0.1.0",
    description="Thin REST wrapper around bd (beads CLI).",
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Phase 1 — Read endpoints
# ---------------------------------------------------------------------------

@app.get("/api/v1/projects")
async def list_projects(_=Depends(require_auth)):
    """List registered projects and whether they have a .beads directory."""
    out = []
    for name, info in PROJECTS.items():
        beads_dir = Path(info["path"]) / ".beads"
        out.append({
            "name": name,
            "prefix": info["prefix"],
            "path": info["path"],
            "has_beads": beads_dir.is_dir(),
        })
    return out


@app.get("/api/v1/beads")
async def list_beads(
    _=Depends(require_auth),
    project: Optional[str] = Query(None, description="Project name (default: os)"),
    status: Optional[str] = Query(None),
    priority: Optional[int] = Query(None),
    label: Optional[str] = Query(None),
    assignee: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    limit: int = Query(50, ge=0, le=500),
    all: bool = Query(False, description="Include closed beads"),
):
    """List beads, optionally filtered."""
    cwd = _project_cwd(project)
    args = ["list", "--json"]
    if all:
        args.append("--all")
    if status:
        args += ["--status", status]
    if priority is not None:
        args += ["--priority", str(priority)]
    if label:
        args += ["--label", label]
    if assignee:
        args += ["--assignee", assignee]
    if type:
        args += ["--type", type]
    if limit:
        args += ["--limit", str(limit)]
    return _run_bd(args, cwd=cwd)


@app.get("/api/v1/beads/{bead_id}")
async def show_bead(
    bead_id: str,
    _=Depends(require_auth),
    project: Optional[str] = Query(None),
):
    """Show details for a single bead."""
    cwd = _project_cwd(project)
    return _run_bd(["show", bead_id, "--json"], cwd=cwd)


@app.get("/api/v1/beads/{bead_id}/comments")
async def list_comments(
    bead_id: str,
    _=Depends(require_auth),
    project: Optional[str] = Query(None),
):
    """List comments on a bead."""
    cwd = _project_cwd(project)
    return _run_bd(["comments", bead_id, "--json"], cwd=cwd)


@app.get("/api/v1/beads/{bead_id}/deps")
async def bead_deps(
    bead_id: str,
    _=Depends(require_auth),
    project: Optional[str] = Query(None),
):
    """Show dependency tree for a bead."""
    cwd = _project_cwd(project)
    return _run_bd(["dep", "tree", bead_id, "--json"], cwd=cwd)


@app.get("/api/v1/artifacts/{path:path}")
async def read_artifact(
    path: str,
    _=Depends(require_auth),
):
    """Read a markdown artifact from a project repo.

    Path format: <project>/path/to/file.md
    Example: 3dl/docs/company-vision.md
    """
    parts = path.split("/", 1)
    if len(parts) != 2:
        raise HTTPException(400, detail="path must be <project>/<filepath>")
    project_name, file_path = parts

    if project_name not in PROJECTS:
        raise HTTPException(404, detail=f"unknown project: {project_name}")

    # Prevent path traversal
    resolved = (Path(PROJECTS[project_name]["path"]) / file_path).resolve()
    project_root = Path(PROJECTS[project_name]["path"]).resolve()
    if not str(resolved).startswith(str(project_root)):
        raise HTTPException(400, detail="path traversal not allowed")

    if not resolved.is_file():
        raise HTTPException(404, detail=f"file not found: {file_path}")

    # Only allow text files
    suffix = resolved.suffix.lower()
    if suffix not in {".md", ".txt", ".yml", ".yaml", ".json", ".toml"}:
        raise HTTPException(400, detail=f"unsupported file type: {suffix}")

    content = resolved.read_text(errors="replace")
    return {"path": path, "content": content}


# ---------------------------------------------------------------------------
# Phase 2 — Write endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/beads")
async def create_bead(
    request: Request,
    _=Depends(require_write_auth),
):
    """Create a new bead.

    Body JSON: { title, description?, priority?, type?, labels?, assignee?, project? }
    """
    body = await request.json()
    title = body.get("title")
    if not title:
        raise HTTPException(400, detail="title is required")

    project = body.get("project")
    cwd = _project_cwd(project)
    actor = body.get("actor", "api")

    args = ["create", title, "--json", "--actor", actor]
    if body.get("description"):
        args += ["--description", body["description"]]
    if body.get("priority") is not None:
        args += ["--priority", str(body["priority"])]
    if body.get("type"):
        args += ["--type", body["type"]]
    if body.get("labels"):
        args += ["--labels", ",".join(body["labels"])]
    if body.get("assignee"):
        args += ["--assignee", body["assignee"]]

    result = _run_bd(args, cwd=cwd)
    # --silent returns just the ID as text
    if isinstance(result, dict) and "output" in result:
        bead_id = result["output"].strip()
        return {"id": bead_id}
    return result


@app.patch("/api/v1/beads/{bead_id}")
async def update_bead(
    bead_id: str,
    request: Request,
    _=Depends(require_write_auth),
):
    """Update a bead.

    Body JSON: { status?, title?, description?, priority?, assignee?,
                 add_labels?, remove_labels?, project?, actor? }
    """
    body = await request.json()
    project = body.get("project")
    cwd = _project_cwd(project)
    actor = body.get("actor", "api")

    args = ["update", bead_id, "--json", "--actor", actor]

    if body.get("status"):
        args += ["--status", body["status"]]
    if body.get("title"):
        args += ["--title", body["title"]]
    if body.get("description"):
        args += ["--description", body["description"]]
    if body.get("priority") is not None:
        args += ["--priority", str(body["priority"])]
    if body.get("assignee"):
        args += ["--assignee", body["assignee"]]
    if body.get("claim"):
        args.append("--claim")
    for label in body.get("add_labels") or []:
        args += ["--add-label", label]
    for label in body.get("remove_labels") or []:
        args += ["--remove-label", label]

    return _run_bd(args, cwd=cwd)


@app.post("/api/v1/beads/{bead_id}/close")
async def close_bead(
    bead_id: str,
    request: Request,
    _=Depends(require_write_auth),
):
    """Close a bead with a reason.

    Body JSON: { reason, project?, actor? }
    """
    body = await request.json()
    reason = body.get("reason", "")
    project = body.get("project")
    cwd = _project_cwd(project)
    actor = body.get("actor", "api")

    args = ["close", bead_id, "--json", "--actor", actor]
    if reason:
        args += ["--reason", reason]

    return _run_bd(args, cwd=cwd)


@app.post("/api/v1/beads/{bead_id}/comments")
async def add_comment(
    bead_id: str,
    request: Request,
    _=Depends(require_write_auth),
):
    """Add a comment to a bead.

    Body JSON: { text, project?, actor? }
    """
    body = await request.json()
    text = body.get("text")
    if not text:
        raise HTTPException(400, detail="text is required")

    project = body.get("project")
    cwd = _project_cwd(project)
    actor = body.get("actor", "api")

    return _run_bd(
        ["comments", "add", bead_id, text, "--actor", actor],
        cwd=cwd,
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=LISTEN_PORT)
