import io
import logging
import re
import requests
import threading
import time
import asyncio
from typing import Callable, Optional, Tuple, Set, Awaitable

logger = logging.getLogger(__name__)
CMD_RE = re.compile(r'^/\w+(@\w+)?(\s|$)')

MAX_TG_MSG = 4096


class Event:
    __slots__ = ("type", "chat", "text", "raw", "command", "args")

    def __init__(self, upd: dict):
        m = upd["message"]
        self.raw = upd
        self.chat = m["chat"]["id"]
        self.text = m.get("text", "")

        if match := CMD_RE.match(self.text):
            self.type = "command"
            self.command = match.group(0).split("@")[0][1:]
            self.args = self.text[match.end():].strip()
            return

        for media, t in (
            ("photo", "photo"),
            ("document", "document"),
            ("voice", "voice"),
            ("video", "video"),
            ("audio", "audio"),
            ("sticker", "sticker"),
            ("contact", "contact"),
        ):
            if media in m:
                self.type, self.command, self.args = t, "", ""
                return

        self.type, self.command, self.args = "text", "", ""


SplitterFn = Callable[[str, int], Tuple[str, int]]
"""Return (visible_part, cut_pos) where cut_pos is the byte index **after** the split.
visible_part may differ from buffer[:cut_pos] (e.g. you replaced a space with …)."""


class _StreamBuffer:
    __slots__ = (
        "bot", "chat", "limit", "splitter", "kw", "_buf", "_pending",
    )

    def __init__(
        self,
        bot: "TelegramBot",
        chat: int,
        limit: int,
        splitter: SplitterFn,
        kw: dict,
    ):
        self.bot = bot
        self.chat = chat
        self.limit = limit
        self.splitter = splitter
        self.kw = kw
        self._buf = io.StringIO()
        self._pending = False

    def write(self, text: str) -> None:
        self._buf.write(text)
        self._pending = True
        if self._buf.tell() >= self.limit:
            self._flush_one()

    def _flush_one(self) -> None:
        """Ask the app where to cut, send that piece, delete it from buffer."""
        if not self._pending:
            return
        raw = self._buf.getvalue()
        visible, cut_pos = self.splitter(raw, self.limit)
        self.bot._raw_send(self.chat, visible, **self.kw)

        # remove the consumed part from buffer
        self._buf = io.StringIO(raw[cut_pos:])
        self._pending = self._buf.tell() > 0

    def flush(self) -> None:
        """Ship whatever is left without further splitting."""
        if not self._pending:
            return
        self.bot._raw_send(self.chat, self._buf.getvalue(), **self.kw)
        self._buf = io.StringIO()
        self._pending = False


class TelegramBot:
    """A minimal Telegram bot implementation.
    
    Args:
        token: The Telegram bot token.
        commands: Optional dictionary of command names to descriptions.
        skip_history: If True (default), skip processing historical messages and only process
                      new messages that arrive while the bot is running.
        offset_file: Optional path to a file where the offset will be persisted
                     between restarts. Only used when skip_history=False.
    
    Example:
        # Only process new messages (default behavior)
        bot = TelegramBot.start("YOUR_BOT_TOKEN")
        bot.run(message_handler)
        
        # Process historical messages but persist offset
        bot = TelegramBot.start("YOUR_BOT_TOKEN", skip_history=False, offset_file="bot_offset.txt")
        bot.run(message_handler)
    """
    def __init__(self, token: str, commands: Optional[dict[str, str]] = None,
                 skip_history: bool = True, offset_file: Optional[str] = None):
        self.token = token
        self.url = f"https://api.telegram.org/bot{token}/"
        self._sess = requests.Session()
        self._cmds = commands
        self._history_skipped = False

        # Handle offset and skip_history logic
        if skip_history:
            # When skipping history, we don't use offset_file for persistence
            self._offset_file = None
            # Initialize offset to 0 temporarily, will be updated by _skip_historical_updates
            self._off = 0
            self._skip_historical_updates()
        else:
            # When not skipping history, use offset_file if provided
            self._offset_file = offset_file
            self._off = self._load_offset(offset_file) if offset_file else 0

    # ------------------ public high-level API ------------------
    @classmethod
    def start(cls, token: str, commands: Optional[dict[str, str]] = None, 
              skip_history: bool = True, offset_file: Optional[str] = None) -> "TelegramBot":
        return cls(token, commands, skip_history, offset_file)

    def run(self, handler: Callable[[Event], None], skip_history: Optional[bool] = None) -> None:
        """Run the bot in the main thread (blocking)."""
        # Skip historical messages if requested (override constructor parameter)
        if skip_history is not None:
            if skip_history and not self._history_skipped:
                self._skip_historical_updates()

        if self._cmds:
            table = [type('C', (), {'name': k, 'help': v})
                     for k, v in self._cmds.items()]
            self.register_commands(table)

        def poll():
            while True:
                try:
                    for u in self._get_updates():
                        handler(Event(u))
                except Exception as e:
                    logger.exception("poll crash: %s", e)
                    time.sleep(1)

        # Run polling directly in the main thread
        try:
            poll()
        except KeyboardInterrupt:
            print("\nBot stopped.")

    # ---------- message sending ----------
    def send(self, chat: int, text: str, **kw) -> None:
        """Plain send; no splitting logic."""
        self._raw_send(chat, text, **kw)

    def typing(self, chat: int) -> None:
        """Send typing indicator (lasts 5 seconds)."""
        self._post("sendChatAction", {"chat_id": chat, "action": "typing"})

    async def keep_typing(self, chat: int, while_running: Callable[[], bool]) -> None:
        """
        Keep sending typing indicator while a condition is true.

        Args:
            chat: Chat ID
            while_running: Function that returns True while typing should continue

        Example:
            streaming = True
            task = asyncio.create_task(bot.keep_typing(chat_id, lambda: streaming))
            # ... do work ...
            streaming = False
            await task
        """
        while while_running():
            self.typing(chat)
            await asyncio.sleep(4)  # Refresh before 5-second expiry

    async def with_typing(
        self,
        chat: int,
        coro: Awaitable,
    ):
        """
        Execute an async operation while showing typing indicator.

        Args:
            chat: Chat ID
            coro: Async operation to execute

        Returns:
            Result of the coroutine

        Example:
            result = await bot.with_typing(chat_id, process_message(text))
        """
        streaming = True
        typing_task = asyncio.create_task(
            self.keep_typing(chat, lambda: streaming)
        )

        try:
            return await coro
        finally:
            streaming = False
            typing_task.cancel()
            try:
                await typing_task
            except asyncio.CancelledError:
                pass

    def stream_to(
        self,
        chat: int,
        *,
        buffer_limit: int = 2048,
        splitter: Optional[SplitterFn] = None,
        **send_kw,
    ) -> _StreamBuffer:
        """
        Return a buffer that auto-flushes when text exceeds buffer_limit.
        `splitter` receives (full_buffer, limit) and returns
        (visible_part, cut_pos_bytes_after_split).
        Default: break at last space before limit and append "…".
        """
        splitter = splitter or self._default_splitter
        return _StreamBuffer(self, chat, buffer_limit, splitter, send_kw)

    def broadcast(self, chats: Set[int], message: str) -> None:
        """
        Send a message to multiple chats.

        Args:
            chats: Set of chat IDs
            message: Message to send
        """
        for chat_id in chats:
            try:
                self.send(chat_id, message)
            except Exception as e:
                logger.warning(f"Failed to send to chat {chat_id}: {e}")

    # ------------------ internal ------------------
    @staticmethod
    def _default_splitter(buf: str, limit: int) -> Tuple[str, int]:
        """Break at last space before limit; append … and point after it."""
        if len(buf) <= limit:
            return buf, len(buf)
        try:
            # find last space inside limit
            cut = buf.rindex(" ", 0, limit)
        except ValueError:
            cut = limit  # no space: hard cut
        visible = buf[:cut].rstrip() + "…"
        return visible, cut + 1  # +1 to skip the space we consumed

    def _raw_send(self, chat: int, text: str, **kw):
        self._post("sendMessage", {"chat_id": chat, "text": text, **kw})

    def register_commands(self, table: list) -> None:
        payload = {
            "commands": [{"command": c.name, "description": c.help} for c in table]
        }
        import json
        self._post("setMyCommands", payload)

    def _skip_historical_updates(self) -> None:
        """Skip all historical updates by getting the latest update_id and setting offset accordingly."""
        # Get the latest update to determine the current update_id
        updates = self._post("getUpdates", {"offset": -1, "limit": 1, "timeout": 1})

        if updates:
            # Set offset to the latest update_id + 1 to skip all historical messages
            latest_update_id = updates[0]["update_id"]
            self._off = latest_update_id + 1
            # Save the offset if we have an offset file configured
            self._save_offset()
        else:
            # No updates available, start from 0 (but this should be rare)
            self._off = 0

        # Set a flag to indicate we've already skipped history
        self._history_skipped = True

    def _load_offset(self, offset_file: str) -> int:
        """Load offset from file, return 0 if file doesn't exist or is invalid."""
        try:
            with open(offset_file, 'r') as f:
                offset = int(f.read().strip())
                return offset if offset > 0 else 0
        except (FileNotFoundError, ValueError, IOError):
            return 0

    def _save_offset(self) -> None:
        """Save current offset to file if offset_file is configured."""
        if self._offset_file and self._off > 0:
            try:
                with open(self._offset_file, 'w') as f:
                    f.write(str(self._off))
            except IOError:
                logger.warning("Failed to save offset to %s", self._offset_file)

    def _get_updates(self):
        r = self._post("getUpdates", {"offset": self._off, "timeout": 30})
        for u in r:
            self._off = u["update_id"] + 1
            yield u
        # Save the offset after processing updates
        self._save_offset()

    def _post(self, method: str, payload: dict):
        for attempt in range(3):
            try:
                rsp = self._sess.post(self.url + method, json=payload, timeout=35)
                rsp.raise_for_status()
            except requests.exceptions.HTTPError as e:
                logger.warning("tg http %s: %s - %s", method, e, rsp.text)
                time.sleep(2 ** attempt)
            except Exception as e:
                logger.warning("tg http %s: %s", method, e)
                time.sleep(2 ** attempt)
            else:
                return rsp.json().get("result", [])
        return []
