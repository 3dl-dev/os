"""Adaptive Card builders for Teams bot responses."""


def _priority_color(priority: int | str | None) -> str:
    p = int(priority) if priority is not None else 9
    if p == 0:
        return "attention"
    if p == 1:
        return "warning"
    return "default"


def _status_emoji(status: str | None) -> str:
    s = (status or "").lower()
    if s in ("closed", "done"):
        return "✅"
    if s == "in_progress":
        return "🔄"
    return "⬚"


def bead_card(bead: dict) -> dict:
    """Build an Adaptive Card for a single bead."""
    bead_id = bead.get("id", bead.get("key", "?"))
    title = bead.get("title", bead.get("summary", "Untitled"))
    status = bead.get("status", "open")
    priority = bead.get("priority", "?")
    assignee = bead.get("assignee", "unassigned")
    bead_type = bead.get("type", "task")
    description = bead.get("description", "")

    # Truncate description for card display
    if len(description) > 300:
        description = description[:297] + "..."

    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "ColumnSet",
                "columns": [
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{
                            "type": "TextBlock",
                            "text": bead_id,
                            "weight": "bolder",
                            "size": "large",
                            "fontType": "monospace",
                        }],
                    },
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [{
                            "type": "TextBlock",
                            "text": title,
                            "wrap": True,
                            "weight": "bolder",
                        }],
                    },
                    {
                        "type": "Column",
                        "width": "auto",
                        "items": [{
                            "type": "TextBlock",
                            "text": f"P{priority}",
                            "color": _priority_color(priority),
                            "weight": "bolder",
                        }],
                    },
                ],
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "Status", "value": f"{_status_emoji(status)} {status}"},
                    {"title": "Type", "value": bead_type},
                    {"title": "Assigned", "value": assignee},
                ],
            },
        ],
        "actions": [],
    }

    if description:
        card["body"].append({
            "type": "TextBlock",
            "text": description,
            "wrap": True,
            "spacing": "small",
            "isSubtle": True,
            "size": "small",
        })

    # Actions based on status
    if status not in ("closed", "done"):
        card["actions"].append({
            "type": "Action.Submit",
            "title": "Claim",
            "data": {"action": "claim", "bead_id": bead_id},
        })
        card["actions"].append({
            "type": "Action.Submit",
            "title": "Close",
            "data": {"action": "close_prompt", "bead_id": bead_id},
        })

    return card


def bead_list_card(beads: list, title: str = "Beads") -> dict:
    """Build an Adaptive Card showing a list of beads."""
    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": title,
                "weight": "bolder",
                "size": "large",
            }
        ],
        "actions": [],
    }

    if not beads:
        card["body"].append({
            "type": "TextBlock",
            "text": "No beads found.",
            "isSubtle": True,
        })
        return card

    for b in beads[:15]:  # Cap at 15 to keep card readable
        bead_id = b.get("id", b.get("key", "?"))
        t = b.get("title", b.get("summary", "Untitled"))
        s = b.get("status", "open")
        p = b.get("priority", "?")
        card["body"].append({
            "type": "ColumnSet",
            "separator": True,
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{
                        "type": "TextBlock",
                        "text": f"`{bead_id}`",
                        "fontType": "monospace",
                        "size": "small",
                    }],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{
                        "type": "TextBlock",
                        "text": f"P{p}",
                        "color": _priority_color(p),
                        "weight": "bolder",
                        "size": "small",
                    }],
                },
                {
                    "type": "Column",
                    "width": "stretch",
                    "items": [{
                        "type": "TextBlock",
                        "text": t,
                        "wrap": True,
                        "size": "small",
                    }],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{
                        "type": "TextBlock",
                        "text": _status_emoji(s),
                        "size": "small",
                    }],
                },
            ],
        })

    if len(beads) > 15:
        card["body"].append({
            "type": "TextBlock",
            "text": f"... and {len(beads) - 15} more",
            "isSubtle": True,
            "size": "small",
        })

    return card


def ready_card(beads: list) -> dict:
    """Build a card specifically for 'ready' results."""
    return bead_list_card(beads, title="Ready Work")


def text_card(text: str, title: str | None = None) -> dict:
    """Simple text response as Adaptive Card."""
    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [],
    }
    if title:
        card["body"].append({
            "type": "TextBlock",
            "text": title,
            "weight": "bolder",
            "size": "medium",
        })
    card["body"].append({
        "type": "TextBlock",
        "text": text,
        "wrap": True,
    })
    return card


def close_prompt_card(bead_id: str) -> dict:
    """Card with input field to collect close reason."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": f"Close {bead_id}",
                "weight": "bolder",
                "size": "medium",
            },
            {
                "type": "Input.Text",
                "id": "close_reason",
                "placeholder": "Reason for closing...",
                "isMultiline": True,
                "isRequired": True,
            },
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Close Bead",
                "style": "positive",
                "data": {"action": "close", "bead_id": bead_id},
            },
        ],
    }


def error_card(message: str) -> dict:
    """Error response card."""
    return text_card(f"⚠️ {message}", title="Error")


def help_card() -> dict:
    """Help card showing available commands."""
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Atom Bot — Commands",
                "weight": "bolder",
                "size": "large",
            },
            {
                "type": "FactSet",
                "facts": [
                    {"title": "ready", "value": "Show actionable work (no blockers)"},
                    {"title": "show <id>", "value": "Show bead details"},
                    {"title": "list [project]", "value": "List open beads"},
                    {"title": "claim <id>", "value": "Claim a bead"},
                    {"title": "done <id> <reason>", "value": "Close a bead"},
                    {"title": "projects", "value": "List registered projects"},
                    {"title": "help", "value": "Show this help"},
                ],
            },
            {
                "type": "TextBlock",
                "text": "You can also use natural phrases like \"what's ready?\" or \"show me os-mjb\".",
                "wrap": True,
                "isSubtle": True,
                "spacing": "medium",
            },
        ],
    }


def projects_card(projects: list) -> dict:
    """Card listing registered projects."""
    card = {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Registered Projects",
                "weight": "bolder",
                "size": "large",
            },
        ],
    }
    for p in projects:
        name = p.get("name", "?")
        prefix = p.get("prefix", "?")
        has_beads = "✅" if p.get("has_beads") else "❌"
        card["body"].append({
            "type": "ColumnSet",
            "separator": True,
            "columns": [
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{"type": "TextBlock", "text": name, "weight": "bolder"}],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{"type": "TextBlock", "text": f"({prefix}-)", "isSubtle": True}],
                },
                {
                    "type": "Column",
                    "width": "auto",
                    "items": [{"type": "TextBlock", "text": has_beads}],
                },
            ],
        })
    return card


def confirmation_card(message: str) -> dict:
    """Simple confirmation card."""
    return text_card(f"✅ {message}")
