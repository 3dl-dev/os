"""HTTP client for the Atom API."""

import aiohttp
from config import API_BASE, API_TOKEN


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


async def api_get(path: str, params: dict | None = None) -> dict | list:
    url = f"{API_BASE}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=_headers(), params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status >= 400:
                text = await resp.text()
                return {"error": True, "status": resp.status, "detail": text}
            return await resp.json()


async def api_post(path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=_headers(), json=body or {}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status >= 400:
                text = await resp.text()
                return {"error": True, "status": resp.status, "detail": text}
            return await resp.json()


async def api_patch(path: str, body: dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=_headers(), json=body or {}, timeout=aiohttp.ClientTimeout(total=15)) as resp:
            if resp.status >= 400:
                text = await resp.text()
                return {"error": True, "status": resp.status, "detail": text}
            return await resp.json()


async def get_bead(bead_id: str, project: str | None = None) -> dict:
    params = {}
    if project:
        params["project"] = project
    return await api_get(f"/api/v1/beads/{bead_id}", params)


async def list_beads(project: str | None = None, status: str | None = None,
                     priority: int | None = None, limit: int = 20) -> list:
    params = {"limit": str(limit)}
    if project:
        params["project"] = project
    if status:
        params["status"] = status
    if priority is not None:
        params["priority"] = str(priority)
    return await api_get("/api/v1/beads", params)


async def list_projects() -> list:
    return await api_get("/api/v1/projects")


async def update_bead(bead_id: str, project: str | None = None, **kwargs) -> dict:
    body = {k: v for k, v in kwargs.items() if v is not None}
    if project:
        body["project"] = project
    body["actor"] = "teams-bot"
    return await api_patch(f"/api/v1/beads/{bead_id}", body)


async def close_bead(bead_id: str, reason: str, project: str | None = None) -> dict:
    body = {"reason": reason, "actor": "teams-bot"}
    if project:
        body["project"] = project
    return await api_post(f"/api/v1/beads/{bead_id}/close", body)


async def create_bead(title: str, project: str | None = None, **kwargs) -> dict:
    body = {"title": title, "actor": "teams-bot"}
    if project:
        body["project"] = project
    body.update({k: v for k, v in kwargs.items() if v is not None})
    return await api_post("/api/v1/beads", body)
