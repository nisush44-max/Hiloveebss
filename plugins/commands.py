import asyncio
import logging
import time

from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, RPCError, UserNotParticipant
from pyrogram.enums import MessageEntityType

from config import LOG_CHANNEL, API_ID, API_HASH, NEW_REQ_MODE, ADMINS
from plugins.database import db
from plugins.rich import RichText, premium_enabled

LOG_TEXT = """<b>#NewUser\n\nID - <code>{}</code>\n\nNᴀᴍᴇ - {}</b>"""
START_IMAGE = "https://te.legra.ph/file/119729ea3cdce4fefb6a1.jpg"


def start_keyboard(username):
    username = (username or "VJJoinRequestBot").lstrip("@")
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Add To Channel", url=f"https://t.me/{username}?startchannel=true"),
            InlineKeyboardButton("➕ Add To Group", url=f"https://t.me/{username}?startgroup=true"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="cmd:help"),
            InlineKeyboardButton("🆘 Support", url="https://t.me/vj_bot_disscussion"),
        ],
        [
            InlineKeyboardButton("📢 Update Channel", url="https://t.me/VJ_Botz"),
            InlineKeyboardButton("👥 Support Group", url="https://t.me/vj_bot_disscussion"),
        ],
        [
            InlineKeyboardButton("🔐 Login", callback_data="cmd:login"),
            InlineKeyboardButton("🚀 Accept", callback_data="cmd:accept"),
            InlineKeyboardButton("📊 Stats", callback_data="cmd:stats"),
        ],
    ])


def build_start_message(name, premium=True):
    r = RichText(premium)
    r.line("╭━━━━━━━━━━━━━━━━━╮")
    r.line("│ ")
    r.add("VJ JOIN REQUEST HUB", MessageEntityType.BOLD)
    r.line("")
    r.line("│ ⚡ Fast • Clean • Secure")
    r.line("╰━━━━━━━━━━━━━━━━━╯")
    r.line("")
    r.add("👋 Welcome ")
    r.add(name, MessageEntityType.BOLD)
    r.line("!")
    r.line("Manage pending channel/group join requests from your own Telegram account with a clean, fast workflow.")
    r.line("")
    r.line("╭──── LIVE FEATURES ─────╮", MessageEntityType.BOLD)
    r.line("│ 🚀 Accept pending join requests")
    r.line("│ 🔗 Channel + Group support")
    r.line("│ 📊 Live success / dead / error stats")
    r.line("│ 💎 Rich premium-emoji interface")
    r.line("│ 🔒 Protected login/session flow")
    r.line("│ 📢 Advanced admin + broadcast tools")
    r.line("╰─────────────────────╯")
    r.line("")
    r.line("╭──── ACCOUNT SNAPSHOT ────╮", MessageEntityType.BOLD)
    r.line("│ 🔐 Login → connect your TG account")
    r.line("│ 🚀 Accept → choose a channel/group")
    r.line("│ 📊 Stats → see today's result table")
    r.line("╰────────────────────────╯")
    r.line("")
    r.line("Use the buttons below to get started.")
    return r.build()


def build_help_message(premium=True):
    r = RichText(premium)
    r.line("╭━━━━━━━━━━━━━━━━━━━╮")
    r.line("│ ", MessageEntityType.BOLD)
    r.add("📚 HELP & QUICK GUIDE", MessageEntityType.BOLD)
    r.line("")
    r.line("╰━━━━━━━━━━━━━━━━━━━━╯")
    r.line("")
    r.line("╭─────── STEPS ───────╮", MessageEntityType.BOLD)
    r.line("   1️⃣ Add the bot as admin to your channel/group.")
    r.line("   2️⃣ Send /login and connect your Telegram account.")
    r.line("   3️⃣ Send /accept or press 🚀 Accept.")
    r.line(".  4️⃣ Forward a message from the target chat.")
    r.line("   5️⃣ Wait for the final rich result report.")
    r.line("╰────────────────────╯")
    r.line("")
    r.line("╭───── COMMANDS ─────╮", MessageEntityType.BOLD)
    r.line("│ 🔐 /login — connect account")
    r.line("│ 🚀 /accept — process pending requests")
    r.line("│ 📊 /mystats — today's result table")
    r.line("│ 🔓 /logout — remove saved session")
    r.line("╰──────────────────────╯")
    r.line("")
    r.line("Need support? Use the 🆘 Support button below.")
    return r.build()


def build_stats_message(stats, title="📊 Today's Join Request Stats", premium=True):
    r = RichText(premium)
    r.line("╭━━━━━━━━━━━━━━━━━━━╮")
    r.line("│ ")
    r.add(title, MessageEntityType.BOLD)
    r.line("")
    r.line("╰━━━━━━━━━━━━━━━━━━━━╯")
    r.line("")
    r.line("╭──── RESULT TABLE ────╮", MessageEntityType.BOLD)
    r.line(f"│ 📨 Total     : {stats.get('total', 0)}")
    r.line(f"│ ✅ Success   : {stats.get('success', 0)}")
    r.line(f"│ 💀 Dead      : {stats.get('dead', 0)}")
    r.line(f"│ ⚠️ Error     : {stats.get('error', 0)}")
    r.line("╰────────────────────╯")
    return r.build()


async def send_rich(client, chat_id, builder_result, **kwargs):
    text, entities = builder_result
    return await client.send_message(chat_id, text, entities=entities, **kwargs)


@Client.on_message(filters.command("start") & filters.private)
async def start_message(c, m):
    if await db.is_banned(m.from_user.id):
        return await m.reply_text("<b>🚫 Your access to this bot has been disabled by an admin.</b>")

    if not await db.is_user_exist(m.from_user.id):
        await db.add_user(m.from_user.id, m.from_user.first_name)
        try:
            await c.send_message(LOG_CHANNEL, LOG_TEXT.format(m.from_user.id, m.from_user.mention))
        except Exception:
            pass
    else:
        await db.touch_user(m.from_user.id, m.from_user.first_name)

    enabled = await premium_enabled(db)
    caption, entities = build_start_message(m.from_user.first_name or "there", enabled)
    await m.reply_photo(
        START_IMAGE,
        caption=caption,
        caption_entities=entities,
        reply_markup=start_keyboard(c.username),
    )


@Client.on_callback_query(filters.regex(r"^cmd:"))
async def command_buttons(client, query):
    if await db.is_banned(query.from_user.id):
        await query.answer("Access disabled.", show_alert=True)
        return
    action = query.data.split(":", 1)[1]
    await query.answer()
    enabled = await premium_enabled(db)

    if action == "help":
        await send_rich(client, query.from_user.id, build_help_message(enabled), reply_markup=start_keyboard(client.username))
    elif action == "login":
        r = RichText(enabled)
        r.line("🔐 ", MessageEntityType.BOLD)
        r.add("Login Required", MessageEntityType.BOLD)
        r.line("")
        r.line("Send /login in this chat to connect your Telegram account securely.")
        await send_rich(client, query.from_user.id, r.build())
    elif action == "accept":
        r = RichText(enabled)
        r.line("🚀 ", MessageEntityType.BOLD)
        r.add("Ready to Accept", MessageEntityType.BOLD)
        r.line("")
        r.line("Send /accept and then forward a message from the channel/group you want to process.")
        await send_rich(client, query.from_user.id, r.build())
    elif action == "stats":
        stats = await db.get_user_stats(query.from_user.id)
        await send_rich(client, query.from_user.id, build_stats_message(stats, premium=enabled))


async def approve_pending_requests(acc, chat_id, owner_id, chat_title, status_msg):
    result = {"attempted": 0, "success": 0, "dead": 0, "error": 0}
    started = time.monotonic()

    while True:
        requests = [r async for r in acc.get_chat_join_requests(chat_id, limit=100)]
        if not requests:
            break

        for req in requests:
            result["attempted"] += 1
            try:
                await acc.approve_chat_join_request(chat_id, req.user.id)
                result["success"] += 1
                await db.record_accept(owner_id, "success", chat_id, chat_title)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await acc.approve_chat_join_request(chat_id, req.user.id)
                    result["success"] += 1
                    await db.record_accept(owner_id, "success", chat_id, chat_title)
                except Exception:
                    result["error"] += 1
                    await db.record_accept(owner_id, "error", chat_id, chat_title)
            except (UserNotParticipant, RPCError):
                result["dead"] += 1
                await db.record_accept(owner_id, "dead", chat_id, chat_title)
            except Exception as exc:
                logging.warning("Join request approval failed for %s: %s", req.user.id, exc)
                result["error"] += 1
                await db.record_accept(owner_id, "error", chat_id, chat_title)

            if result["attempted"] % 20 == 0:
                elapsed = int(time.monotonic() - started)
                try:
                    await status_msg.edit_text(
                        "<b>⚡ Processing join requests...</b>\n\n"
                        f"📨 Attempted: <code>{result['attempted']}</code>\n"
                        f"✅ Success: <code>{result['success']}</code>\n"
                        f"💀 Dead: <code>{result['dead']}</code>\n"
                        f"⚠️ Error: <code>{result['error']}</code>\n"
                        f"⏱ Time: <code>{elapsed}s</code>"
                    )
                except Exception:
                    pass
    return result, int(time.monotonic() - started)


async def build_accept_report(result, seconds, chat_title, chat_type, stats, premium=True):
    r = RichText(premium)
    r.line("╭━━━━━━━━━━━━━━━━━━╮")
    r.line("│ ", MessageEntityType.BOLD)
    r.add("🎉 ACCEPT COMPLETE", MessageEntityType.BOLD)
    r.line("")
    r.line("╰━━━━━━━━━━━━━━━━━━╯")
    r.line("")
    r.line("╭──── TARGET ─────╮", MessageEntityType.BOLD)
    r.line(f"│ 📣 {chat_title}")
    r.line(f"│ 🗂 Type     : {chat_type}")
    r.line("╰────────────────╯")
    r.line("")
    r.line("╭──── RESULT TABLE ────╮", MessageEntityType.BOLD)
    r.line(f"│ 📨 Total     : {result['attempted']}")
    r.line(f"│ ✅ Success   : {result['success']}")
    r.line(f"│ 💀 Dead      : {result['dead']}")
    r.line(f"│ ⚠️ Error     : {result['error']}")
    r.line(f"│ ⏱ Time      : {seconds}s")
    r.line("╰─────────────────────────╯")
    r.line("")
    r.line("╭── TODAY YOUR ACCOUNT ───╮", MessageEntityType.BOLD)
    r.line(f"│ 📊 Total     : {stats.get('total', 0)}")
    r.line(f"│ ✅ Success   : {stats.get('success', 0)}")
    r.line(f"│ 💀 Dead      : {stats.get('dead', 0)}")
    r.line(f"│ ⚠️ Error     : {stats.get('error', 0)}")
    r.line("╰─────────────────────────╯")
    return r.build()


@Client.on_message(filters.command("accept") & filters.private)
async def accept(client, message):
    if await db.is_banned(message.from_user.id):
        return await message.reply_text("<b>🚫 Your access to this bot has been disabled by an admin.</b>")
    show = await message.reply_text("<b>⏳ Please wait...</b>")
    await db.touch_user(message.from_user.id, message.from_user.first_name)
    user_data = await db.get_session(message.from_user.id)
    if user_data is None:
        await show.edit_text("<b>❌ Please /login first to accept pending requests.</b>")
        return

    acc = Client(
        f"joinrequest_{message.from_user.id}",
        session_string=user_data,
        api_hash=API_HASH,
        api_id=API_ID,
        in_memory=True,
    )
    try:
        await acc.connect()
    except Exception:
        await show.edit_text("<b>❌ Your login session expired. Use /logout and then /login again.</b>")
        return

    try:
        await show.edit_text(
            "<b>📩 Forward a message from your channel or group.</b>\n\n"
            "Make sure the logged-in account is an admin there with permission to manage join requests."
        )
        vj = await client.listen(message.chat.id, timeout=300)
        if not vj.forward_from_chat or vj.forward_from_chat.type in [enums.ChatType.PRIVATE, enums.ChatType.BOT]:
            await show.edit_text("<b>❌ Message was not forwarded from a channel/group.</b>")
            return

        chat_id = vj.forward_from_chat.id
        try:
            info = await acc.get_chat(chat_id)
        except Exception:
            await show.edit_text("<b>❌ The logged-in account is not an admin or cannot access this channel/group.</b>")
            return

        try:
            await vj.delete()
        except Exception:
            pass

        chat_title = info.title or "Unknown Chat"
        chat_type = "Channel" if info.type == enums.ChatType.CHANNEL else "Group"
        await show.edit_text(
            f"<b>🚀 Starting...</b>\n\nChat: <b>{chat_title}</b>\nType: <b>{chat_type}</b>"
        )

        result, seconds = await approve_pending_requests(acc, chat_id, message.from_user.id, chat_title, show)
        stats = await db.get_user_stats(message.from_user.id)
        enabled = await premium_enabled(db)
        report = await build_accept_report(result, seconds, chat_title, chat_type, stats, enabled)
        await show.edit_text(report[0], entities=report[1], reply_markup=start_keyboard(client.username))

        # A separate DM report, so the account owner receives a persistent result
        # even if the progress message was edited or removed later.
        try:
            await send_rich(client, message.from_user.id, report)
        except Exception:
            pass
    except asyncio.TimeoutError:
        await show.edit_text("<b>⌛ Timed out. Send /accept again when you are ready.</b>")
    except Exception as e:
        logging.exception("accept failed")
        try:
            await show.edit_text(f"<b>❌ Error:</b> <code>{str(e)[:700]}</code>")
        except Exception:
            pass
    finally:
        try:
            await acc.disconnect()
        except Exception:
            pass


@Client.on_message(filters.command("mystats") & filters.private)
async def my_stats(client, message):
    if await db.is_banned(message.from_user.id):
        return await message.reply_text("<b>🚫 Your access to this bot has been disabled by an admin.</b>")
    stats = await db.get_user_stats(message.from_user.id)
    enabled = await premium_enabled(db)
    await send_rich(client, message.from_user.id, build_stats_message(stats, premium=enabled))


@Client.on_chat_join_request(filters.group | filters.channel)
async def approve_new(client, m):
    if not NEW_REQ_MODE:
        return
    try:
        await client.approve_chat_join_request(m.chat.id, m.from_user.id)
        try:
            await client.send_message(
                m.from_user.id,
                f"<b>✅ Your join request for {m.chat.title} was accepted.</b>\n\nPowered By @VJ_Botz",
            )
        except Exception:
            pass
    except Exception as e:
        logging.warning("Auto approval failed: %s", e)
