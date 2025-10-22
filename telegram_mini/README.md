# telegram-mini

Minimal Telegram bot client with polling, send/edit/delete, inline keyboards, typing indicators, and buffered streaming.

Features:
- `TelegramBot.start(token, commands=..., skip_history=True, offset_file=None, auth_gate=None)` and `run(handler)` for polling.
- Helpers: `inline_keyboard`, `typing`/`keep_typing`/`with_typing`, `stream_to(...)`, `edit_message_text`, `delete_message`, `answer_callback_query`.

Quick start:
```python
from telegram_mini import TelegramBot

bot = TelegramBot.start("<BOT_TOKEN>")
bot.run(lambda ev: bot.send(ev.chat, f"You said: {ev.text}"))
```

Install (editable):
uv add -e ../libs/telegram_mini
