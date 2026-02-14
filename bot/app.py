"""Atom Teams Bot — aiohttp web server entry point.

Receives Bot Framework activities from Azure Bot Service and dispatches
to the AtomBot handler.
"""

import sys
import traceback

from aiohttp import web
from botbuilder.core import (
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
    TurnContext,
)
from botbuilder.schema import Activity

import config
from bot import AtomBot

# Adapter
settings = BotFrameworkAdapterSettings(
    app_id=config.APP_ID,
    app_password=config.APP_PASSWORD,
)
adapter = BotFrameworkAdapter(settings)


async def on_error(context: TurnContext, error: Exception):
    """Global error handler for the bot adapter."""
    print(f"[bot error] {error}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    await context.send_activity("Sorry, something went wrong. Check bot logs.")


adapter.on_turn_error = on_error

# Bot instance
bot = AtomBot()


# ---- Routes ----

async def messages(request: web.Request) -> web.Response:
    """Main messaging endpoint — receives Bot Framework activities."""
    if "application/json" not in (request.content_type or ""):
        return web.Response(status=415, text="Unsupported media type")

    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")

    response = await adapter.process_activity(activity, auth_header, bot.on_turn)

    if response:
        return web.json_response(data=response.body, status=response.status)
    return web.Response(status=201)


async def health(request: web.Request) -> web.Response:
    """Health check."""
    return web.json_response({"status": "ok", "service": "atom-teams-bot"})


# ---- App ----

app = web.Application()
app.router.add_post("/api/messages", messages)
app.router.add_get("/healthz", health)


if __name__ == "__main__":
    print(f"Starting Atom Teams Bot on port {config.BOT_PORT}...")
    print(f"  Messaging endpoint: http://0.0.0.0:{config.BOT_PORT}/api/messages")
    print(f"  Atom API: {config.API_BASE}")
    print(f"  Azure App ID: {config.APP_ID[:8]}..." if config.APP_ID else "  Azure App ID: (not set — dev mode)")
    web.run_app(app, host="0.0.0.0", port=config.BOT_PORT)
