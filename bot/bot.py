"""Teams activity handler — command parsing and card action routing."""

import re
from botbuilder.core import TurnContext, CardFactory
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.core.teams import TeamsActivityHandler

import api_client as api
import cards


# Regex patterns for bead IDs (e.g., os-mjb, 3dl-k3e)
BEAD_ID_RE = re.compile(r"\b([a-z0-9]+-[a-z0-9]+)\b")


def _extract_bead_id(text: str) -> str | None:
    """Try to extract a bead ID from text."""
    m = BEAD_ID_RE.search(text)
    return m.group(1) if m else None


def _extract_project(text: str) -> str | None:
    """Extract project name if mentioned."""
    projects = ["os", "3dl", "website", "mag-shield", "galtrader", "vms"]
    lower = text.lower()
    for p in projects:
        if p in lower:
            return p
    return None


def _strip_mention(text: str) -> str:
    """Remove @mention tags from Teams message text."""
    # Teams wraps mentions in <at>...</at> tags
    cleaned = re.sub(r"<at>.*?</at>", "", text).strip()
    return cleaned


class AtomBot(TeamsActivityHandler):
    """Main bot handler for Teams interactions."""

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages — parse commands, dispatch to handlers."""
        raw_text = turn_context.activity.text or ""
        text = _strip_mention(raw_text).strip()

        if not text:
            return

        lower = text.lower()

        # Route to command handlers
        if lower in ("help", "?", "commands"):
            await self._send_card(turn_context, cards.help_card())

        elif lower in ("ready", "what's ready", "whats ready", "what is ready"):
            await self._handle_ready(turn_context)

        elif lower.startswith("show ") or lower.startswith("bead "):
            bead_id = _extract_bead_id(text)
            if bead_id:
                await self._handle_show(turn_context, bead_id)
            else:
                await self._send_card(turn_context, cards.error_card("No bead ID found. Usage: show <bead-id>"))

        elif lower.startswith("list"):
            project = _extract_project(text)
            await self._handle_list(turn_context, project)

        elif lower.startswith("claim "):
            bead_id = _extract_bead_id(text)
            if bead_id:
                await self._handle_claim(turn_context, bead_id)
            else:
                await self._send_card(turn_context, cards.error_card("No bead ID found. Usage: claim <bead-id>"))

        elif lower.startswith("done ") or lower.startswith("close "):
            bead_id = _extract_bead_id(text)
            if bead_id:
                # Check if reason is provided inline
                parts = text.split(None, 2)
                if len(parts) >= 3:
                    reason = parts[2] if not BEAD_ID_RE.match(parts[2]) else ""
                    # The reason might start after the bead ID
                    idx = text.find(bead_id)
                    if idx >= 0:
                        reason = text[idx + len(bead_id):].strip()
                    if reason:
                        await self._handle_close(turn_context, bead_id, reason)
                        return
                # No inline reason — prompt for one
                await self._send_card(turn_context, cards.close_prompt_card(bead_id))
            else:
                await self._send_card(turn_context, cards.error_card("No bead ID found. Usage: done <bead-id> [reason]"))

        elif lower in ("projects", "repos"):
            await self._handle_projects(turn_context)

        elif lower.startswith("status"):
            project = _extract_project(text)
            await self._handle_status(turn_context, project)

        else:
            # Try to detect a bead ID in freeform text
            bead_id = _extract_bead_id(text)
            if bead_id:
                await self._handle_show(turn_context, bead_id)
            else:
                await self._send_card(turn_context, cards.text_card(
                    "I didn't understand that. Type **help** to see available commands.",
                    title="Atom",
                ))

    async def on_teams_card_action(self, turn_context: TurnContext) -> None:
        """Handle Adaptive Card Action.Submit buttons."""
        data = turn_context.activity.value or {}
        action = data.get("action")

        if action == "claim":
            bead_id = data.get("bead_id", "")
            await self._handle_claim(turn_context, bead_id)

        elif action == "close_prompt":
            bead_id = data.get("bead_id", "")
            await self._send_card(turn_context, cards.close_prompt_card(bead_id))

        elif action == "close":
            bead_id = data.get("bead_id", "")
            reason = data.get("close_reason", "Closed via Teams")
            await self._handle_close(turn_context, bead_id, reason)

    async def on_invoke_activity(self, turn_context: TurnContext):
        """Handle invoke activities (card actions come through here in Teams)."""
        activity = turn_context.activity
        if activity.name == "adaptiveCard/action":
            data = (activity.value or {}).get("action", {}).get("data", {})
            action = data.get("action")
            if action == "claim":
                await self._handle_claim(turn_context, data.get("bead_id", ""))
            elif action == "close_prompt":
                await self._send_card(turn_context, cards.close_prompt_card(data.get("bead_id", "")))
            elif action == "close":
                await self._handle_close(turn_context, data.get("bead_id", ""), data.get("close_reason", "Closed via Teams"))
            return self._create_invoke_response(200)
        return await super().on_invoke_activity(turn_context)

    # ---- Command handlers ----

    async def _handle_ready(self, turn_context: TurnContext):
        """Show ready work across all projects."""
        # The API doesn't have a /ready endpoint — use list with status filter
        # For now, get open beads sorted by priority
        result = await api.list_beads(status="open", limit=20)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(result.get("detail", "API error")))
            return
        beads = result if isinstance(result, list) else result.get("issues", result.get("beads", []))
        await self._send_card(turn_context, cards.ready_card(beads))

    async def _handle_show(self, turn_context: TurnContext, bead_id: str):
        """Show details for a single bead."""
        # Guess project from bead prefix
        project = self._project_from_bead_id(bead_id)
        result = await api.get_bead(bead_id, project=project)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(f"Bead {bead_id}: {result.get('detail', 'not found')}"))
            return
        await self._send_card(turn_context, cards.bead_card(result))

    async def _handle_list(self, turn_context: TurnContext, project: str | None):
        """List open beads, optionally filtered by project."""
        result = await api.list_beads(project=project, limit=20)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(result.get("detail", "API error")))
            return
        beads = result if isinstance(result, list) else result.get("issues", result.get("beads", []))
        title = f"Open Beads — {project}" if project else "Open Beads"
        await self._send_card(turn_context, cards.bead_list_card(beads, title=title))

    async def _handle_claim(self, turn_context: TurnContext, bead_id: str):
        """Claim a bead (set status to in_progress, assign to current user)."""
        project = self._project_from_bead_id(bead_id)
        result = await api.update_bead(bead_id, project=project, status="in_progress", claim=True)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(f"Failed to claim {bead_id}: {result.get('detail', 'error')}"))
            return
        await self._send_card(turn_context, cards.confirmation_card(f"Claimed **{bead_id}** — status set to in_progress"))

    async def _handle_close(self, turn_context: TurnContext, bead_id: str, reason: str):
        """Close a bead with reason."""
        project = self._project_from_bead_id(bead_id)
        result = await api.close_bead(bead_id, reason=reason, project=project)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(f"Failed to close {bead_id}: {result.get('detail', 'error')}"))
            return
        await self._send_card(turn_context, cards.confirmation_card(f"Closed **{bead_id}**: {reason}"))

    async def _handle_projects(self, turn_context: TurnContext):
        """List registered projects."""
        result = await api.list_projects()
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(result.get("detail", "API error")))
            return
        projects = result if isinstance(result, list) else []
        await self._send_card(turn_context, cards.projects_card(projects))

    async def _handle_status(self, turn_context: TurnContext, project: str | None):
        """Show project status summary."""
        result = await api.list_beads(project=project, limit=50)
        if isinstance(result, dict) and result.get("error"):
            await self._send_card(turn_context, cards.error_card(result.get("detail", "API error")))
            return
        beads = result if isinstance(result, list) else result.get("issues", result.get("beads", []))

        # Count by status
        counts = {}
        for b in beads:
            s = b.get("status", "open")
            counts[s] = counts.get(s, 0) + 1

        summary_lines = [f"**{s}**: {c}" for s, c in sorted(counts.items())]
        summary = "\n".join(summary_lines) if summary_lines else "No beads found."
        title = f"Status — {project}" if project else "Status — All Projects"
        await self._send_card(turn_context, cards.text_card(summary, title=title))

    # ---- Helpers ----

    async def _send_card(self, turn_context: TurnContext, card_content: dict):
        """Send an Adaptive Card as a response."""
        attachment = CardFactory.adaptive_card(card_content)
        activity = Activity(
            type=ActivityTypes.message,
            attachments=[attachment],
        )
        await turn_context.send_activity(activity)

    @staticmethod
    def _project_from_bead_id(bead_id: str) -> str | None:
        """Guess project from bead ID prefix."""
        prefix_map = {
            "os": "os",
            "3dl": "3dl",
            "website": "website",
            "mag": "mag-shield",
            "galtrader": "galtrader",
            "vms": "vms",
        }
        parts = bead_id.split("-", 1)
        if parts[0] in prefix_map:
            return prefix_map[parts[0]]
        return None

    @staticmethod
    def _create_invoke_response(status_code: int):
        from botbuilder.core import InvokeResponse
        return InvokeResponse(status=status_code)
