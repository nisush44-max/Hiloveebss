import datetime
import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMINS, NEW_REQ_MODE
from plugins.database import db
from plugins.rich import RichText, premium_enabled

START_TIME = time.monotonic()
ADMIN_IDS = set(ADMINS if isinstance(ADMINS, (list, tuple, set)) else [ADMINS])


def panel():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 Overview", callback_data="adm:overview"), InlineKeyboardButton("📈 Today", callback_data="adm:today")],
        [InlineKeyboardButton("👥 Users", callback_data="adm:users"), InlineKeyboardButton("🔐 Sessions", callback_data="adm:sessions")],
        [InlineKeyboardButton("🏆 Top Users", callback_data="adm:top"), InlineKeyboardButton("📝 Recent Accepts", callback_data="adm:recent")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="adm:broadcast"), InlineKeyboardButton("📜 Broadcast History", callback_data="adm:broadcasts")],
        [InlineKeyboardButton("⚡ Auto Mode", callback_data="adm:automode"), InlineKeyboardButton("✨ Premium Emojis", callback_data="adm:premium")],
        [InlineKeyboardButton("🗄 DB Health", callback_data="adm:db"), InlineKeyboardButton("🧩 DB Collections", callback_data="adm:collections")],
        [InlineKeyboardButton("⏱ Uptime", callback_data="adm:uptime"), InlineKeyboardButton("ℹ️ Bot Info", callback_data="adm:info")],
        [InlineKeyboardButton("📅 7 Day", callback_data="adm:7day"), InlineKeyboardButton("📆 Yesterday", callback_data="adm:yesterday")],
        [InlineKeyboardButton("🗓 30 Day", callback_data="adm:30day"), InlineKeyboardButton("🔥 Active Users", callback_data="adm:active")],
        [InlineKeyboardButton("⚙️ Config", callback_data="adm:config"), InlineKeyboardButton("📚 Admin Help", callback_data="adm:help")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="adm:overview"), InlineKeyboardButton("❌ Close", callback_data="adm:close")],
    ])


def is_admin(user_id):
    return int(user_id) in ADMIN_IDS


def fmt_uptime():
    seconds = int(time.monotonic() - START_TIME)
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, s = divmod(seconds, 60)
    return f"{d}d {h}h {m}m {s}s"


async def admin_rich(title, lines, premium=True):
    r = RichText(premium)
    r.line("╭━━━━━━━━━━━━━━━━━━━━━━━━╮")
    r.line("│ ")
    r.add(title, style=None)
    r.line("")
    r.line("╰━━━━━━━━━━━━━━━━━━━━━━━━╯")
    r.line("")
    for line in lines:
        r.line(line)
    return r.build()


@Client.on_message(filters.command("admin") & filters.private & filters.user(ADMINS))
async def admin_command(client, message):
    await message.reply_text("<b>🛠 Advanced Admin Panel</b>\n\nChoose an option:", reply_markup=panel())


@Client.on_message(filters.command("stats") & filters.private & filters.user(ADMINS))
async def admin_stats(client, message):
    s = await db.get_global_stats()
    enabled = await premium_enabled(db)
    text, entities = await admin_rich("📊 GLOBAL TODAY STATS", [
        f"👥 Users       : {await db.total_users_count()}",
        f"🔐 Sessions    : {await db.active_sessions_count()}",
        f"📨 Requests    : {s.get('total', 0)}",
        f"✅ Success     : {s.get('success', 0)}",
        f"💀 Dead        : {s.get('dead', 0)}",
        f"⚠️ Error       : {s.get('error', 0)}",
        f"⚡ Auto Mode   : {'ON' if NEW_REQ_MODE else 'OFF'}",
        f"✨ Premium UI  : {'ON' if enabled else 'OFF'}",
        f"⏱ Uptime      : {fmt_uptime()}",
    ], enabled)
    await message.reply_text(text, entities=entities, reply_markup=panel())


@Client.on_message(filters.command("ban") & filters.private & filters.user(ADMINS))
async def ban_user(client, message):
    if len(message.command) < 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/ban USER_ID</code>")
    uid = int(message.command[1])
    await db.set_ban(uid, "Admin ban")
    await message.reply_text(f"<b>🚫 User banned:</b> <code>{uid}</code>")


@Client.on_message(filters.command("unban") & filters.private & filters.user(ADMINS))
async def unban_user(client, message):
    if len(message.command) < 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/unban USER_ID</code>")
    uid = int(message.command[1])
    await db.remove_ban(uid)
    await message.reply_text(f"<b>✅ User unbanned:</b> <code>{uid}</code>")


async def render_admin(action):
    enabled = await premium_enabled(db)
    if action in ("overview", "today"):
        s = await db.get_global_stats()
        return await admin_rich("📊 ADMIN OVERVIEW", [
            f"👥 Total Users       : {await db.total_users_count()}",
            f"🔐 Logged-in         : {await db.active_sessions_count()}",
            f"📨 Today's Requests : {s.get('total', 0)}",
            f"✅ Success           : {s.get('success', 0)}",
            f"💀 Dead              : {s.get('dead', 0)}",
            f"⚠️ Errors            : {s.get('error', 0)}",
            f"⚡ Auto Approval     : {'ON' if NEW_REQ_MODE else 'OFF'}",
            f"✨ Premium Emojis    : {'ON' if enabled else 'OFF'}",
            f"⏱ Uptime             : {fmt_uptime()}",
        ], enabled)
    if action == "users":
        users = await db.get_recent_users(10)
        lines = [f"👥 Recent Users ({len(users)})"]
        for u in users:
            lines.append(f"• {u.get('id')} — {u.get('name','Unknown')}")
        return await admin_rich("👥 USERS", lines, enabled)
    if action == "sessions":
        return await admin_rich("🔐 SESSIONS", [f"Connected Telegram accounts: {await db.active_sessions_count()}"], enabled)
    if action == "top":
        rows = await db.get_top_users(limit=10)
        lines = ["Today's highest-success accounts:"]
        for i, row in enumerate(rows, 1):
            lines.append(f"{i}. {row.get('user_id')} — ✅ {row.get('success',0)} | 💀 {row.get('dead',0)} | ⚠️ {row.get('error',0)}")
        return await admin_rich("🏆 TOP USERS", lines, enabled)
    if action == "recent":
        rows = await db.get_recent_accepts(12)
        lines = ["Latest acceptance activity:"]
        for row in rows:
            title = row.get("chat_title") or "Unknown"
            lines.append(f"• {row.get('user_id')} | {row.get('status')} | {title} | +{row.get('amount',1)}")
        return await admin_rich("📝 RECENT ACCEPTS", lines, enabled)
    if action == "broadcasts":
        rows = await db.get_broadcasts(10)
        lines = ["Latest broadcast runs:"]
        for row in rows:
            lines.append(f"• {row.get('started_at')} | ✅ {row.get('success',0)} | 🚫 {row.get('blocked',0)} | ⚠️ {row.get('failed',0)}")
        return await admin_rich("📜 BROADCAST HISTORY", lines, enabled)
    if action == "broadcast":
        return await admin_rich("📢 BROADCAST", [
            "Reply to any message with /broadcast in this private chat.",
            "Only configured admins can use it.",
            "Final report includes total, completed, success, blocked, deleted and failed counts.",
        ], enabled)
    if action == "automode":
        return await admin_rich("⚡ AUTO JOIN REQUEST MODE", [f"Current: {'ON' if NEW_REQ_MODE else 'OFF'}", "Controlled by NEW_REQ_MODE at startup."], enabled)
    if action == "premium":
        state = "ON" if enabled else "OFF"
        return await admin_rich("✨ PREMIUM EMOJI MODE", [f"Current: {state}", "ON = use one matching custom emoji ID from emojisid.txt.", "OFF = show only the normal fallback emoji.", "Press the button below to toggle."], enabled)
    if action == "db":
        try:
            await db.db_ping()
            return await admin_rich("🗄 DATABASE HEALTH", ["✅ MongoDB ping successful.", "✅ Database connection is responding."], enabled)
        except Exception as e:
            return await admin_rich("🗄 DATABASE HEALTH", [f"❌ MongoDB error: {str(e)[:700]}"], enabled)
    if action == "uptime":
        return await admin_rich("⏱ BOT UPTIME", [fmt_uptime()], enabled)
    if action == "info":
        return await admin_rich("ℹ️ BOT INFO", ["Join Request Acceptor", "Pyrofork + MongoDB", "Rich custom emoji UI", "Admin tools + broadcast + per-user statistics"], enabled)
    if action in ("7day", "30day"):
        days = 7 if action == "7day" else 30
        today = datetime.datetime.now(datetime.timezone.utc).date()
        total = success = dead = error = 0
        for i in range(days):
            day = (today - datetime.timedelta(days=i)).strftime("%Y-%m-%d")
            s = await db.get_global_stats(day)
            total += s.get("total", 0); success += s.get("success", 0); dead += s.get("dead", 0); error += s.get("error", 0)
        return await admin_rich(f"📅 LAST {days} DAYS", [f"📨 Total  : {total}", f"✅ Success: {success}", f"💀 Dead   : {dead}", f"⚠️ Error  : {error}"], enabled)
    if action == "yesterday":
        day = (datetime.datetime.now(datetime.timezone.utc).date() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        s = await db.get_global_stats(day)
        return await admin_rich(f"📆 YESTERDAY ({day})", [f"📨 Total  : {s.get('total',0)}", f"✅ Success: {s.get('success',0)}", f"💀 Dead   : {s.get('dead',0)}", f"⚠️ Error  : {s.get('error',0)}"], enabled)
    if action == "active":
        now = datetime.datetime.now(datetime.timezone.utc)
        count = await db.col.count_documents({"last_seen": {"$gte": now - datetime.timedelta(days=1)}})
        return await admin_rich("🔥 ACTIVE USERS", [f"Users active in the last 24 hours: {count}"], enabled)
    if action == "collections":
        names = await db.db.list_collection_names()
        return await admin_rich("🧩 MONGODB COLLECTIONS", names or ["No collections found."], enabled)
    if action == "config":
        return await admin_rich("⚙️ CONFIG STATUS", [
            f"👑 Admin IDs     : {len(ADMIN_IDS)}",
            f"⚡ NEW_REQ_MODE : {'ON' if NEW_REQ_MODE else 'OFF'}",
            "🔐 DB URI        : configured",
            "🤖 Bot Token     : configured",
            f"✨ Premium UI    : {'ON' if enabled else 'OFF'}",
        ], enabled)
    if action == "help":
        return await admin_rich("📚 ADMIN HELP", [
            "/admin — open panel",
            "/stats — global daily stats",
            "/broadcast — reply to a message to broadcast it",
            "/ban USER_ID — ban a bot user",
            "/unban USER_ID — remove a bot-user ban",
            "Premium Emojis toggles the rich custom-emoji renderer globally.",
        ], enabled)
    return await admin_rich("🛠 ADVANCED ADMIN PANEL", ["Choose an option from the buttons below."], enabled)


def premium_panel_keyboard(enabled):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✨ Premium Emojis: {'ON' if enabled else 'OFF'}", callback_data="adm:toggle_premium")],
        [InlineKeyboardButton("⬅️ Back", callback_data="adm:overview")],
    ])


@Client.on_callback_query(filters.regex(r"^adm:"))
async def admin_callback(client, query):
    if not is_admin(query.from_user.id):
        await query.answer("Admin only.", show_alert=True)
        return
    action = query.data.split(":", 1)[1]
    if action == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            pass
        return
    if action == "toggle_premium":
        current = await premium_enabled(db)
        await db.set_setting("premium_emojis", not current)
        enabled = not current
        await query.answer(f"Premium emoji mode {'enabled' if enabled else 'disabled'}")
        text, entities = await render_admin("premium")
        await query.message.edit_text(text, entities=entities, reply_markup=premium_panel_keyboard(enabled))
        return
    await query.answer()
    text, entities = await render_admin(action)
    markup = premium_panel_keyboard(await premium_enabled(db)) if action == "premium" else panel()
    await query.message.edit_text(text, entities=entities, reply_markup=markup)
