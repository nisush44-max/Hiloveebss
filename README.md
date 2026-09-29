# VJ Join Request Acceptor Bot — Advanced Rich UI

This version keeps the original join-request workflow and adds a rich Telegram UI.

## Main features
- Channel + Group join-request acceptance
- User Telegram account login/session flow
- `/accept`, `/mystats`, `/logout`
- Final acceptance report in the chat **and a separate DM**
- Today: total / success / dead / error statistics
- Advanced admin panel and broadcast tools
- Premium custom-emoji rich messages using the supplied `emojisid.txt`
- Premium emoji mode can be toggled from `/admin`
- When Premium Emoji mode is OFF, the same messages use normal fallback emojis only
- When an emoji is not present in the supplied list, the renderer uses a suitable supported visual fallback; it never creates a second normal+premium emoji pair
- Rich photo start message with boxed/table-style text
- URL buttons for Add To Channel, Add To Group, Update Channel and Support Group
- Callback/command-style buttons for Help, Login, Accept and Stats

## Environment variables
`API_ID`, `API_HASH`, `BOT_TOKEN`, `DB_URI`, `DB_NAME`, `LOG_CHANNEL`, `ADMINS`, `NEW_REQ_MODE`

## Render
Recommended start command:

```bash
gunicorn app:app & python3 bot.py
```

Python version is pinned in `.python-version`.

## Premium emoji implementation
Telegram custom emojis are sent as `MessageEntity` objects with `CUSTOM_EMOJI` and a `custom_emoji_id`. The entity wraps the matching regular fallback emoji, as required by Telegram.
