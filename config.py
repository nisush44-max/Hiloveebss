from os import environ

API_ID = int(environ.get("API_ID", "0"))
API_HASH = environ.get("API_HASH", "")
BOT_TOKEN = environ.get("BOT_TOKEN", "")

LOG_CHANNEL = int(environ.get("LOG_CHANNEL", "0"))

# Supports one admin ID or comma-separated IDs: 123,456,789
_raw_admins = environ.get("ADMINS", "0")
ADMINS = [int(x.strip()) for x in _raw_admins.split(",") if x.strip().lstrip("-").isdigit()]
if not ADMINS:
    ADMINS = [0]

DB_URI = environ.get("DB_URI", "")
DB_NAME = environ.get("DB_NAME", "vjjoinrequetbot")
NEW_REQ_MODE = environ.get("NEW_REQ_MODE", "false").strip().lower() in ("1", "true", "yes", "on")
