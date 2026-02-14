"""Bot configuration from environment variables."""

import os

# Azure Bot registration
APP_ID = os.environ.get("AZURE_APP_ID", "")
APP_PASSWORD = os.environ.get("AZURE_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("AZURE_TENANT_ID", "")

# Atom API
API_BASE = os.environ.get("ATOM_API_URL", "http://localhost:3131")
API_TOKEN = os.environ.get("ATOM_API_TOKEN", "")

# Bot server
BOT_PORT = int(os.environ.get("BOT_PORT", "3978"))
