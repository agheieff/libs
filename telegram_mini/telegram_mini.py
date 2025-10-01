import io
import os
import logging
import re
import requests
import threading
import time
import asyncio
from typing import Callable, Optional, Tuple, Set, Awaitable

logger = logging.getLogger(__name__)
_DEBUG = os.getenv("TELEGRAM_MINI_DEBUG", "").lower() in ("1", "true", "yes", "on")
CMD_RE = re.compile(r'^/\w+(@\w+)?(\s|$)')

MAX_TG_MSG = 4096


class Event:
    __slots__ = ("type", "chat", "text", "raw", "command", "args",
                 "user_id", "username", "first_name", "last_name", "message_id")

    def __init__(self, upd: dict):
        self.raw = upd

        # Handle both regular messages and callback queries
        if "message" in upd:
            m = upd["message"]
            self.chat = m["chat"]["id"]
            self.text = m.get("text", "")
            self.message_id = m["message_id"]

            # Extract user information
            user = m.get("from", {})
            self.user_id = user.get("id")
            self.username = user.get("username")
            self.first_name = user.get("first_name")
            self.last_name = user.get("last_name")

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

        elif "callback_query" in upd:
            # Handle callback queries from inline buttons
            cb = upd["callback_query"]
            self.type = "callback_query"
            self.chat = cb["message"]["chat"]["id"]
            self.message_id = cb["message"]["message_id"]
            self.text = cb.get("data", "")
            self.command = ""
            self.args = ""

            # Extract user information
            user = cb.get("from", {})
            self.user_id = user.get("id")
            self.username = user.get("username")
            self.first_name = user.get("first_name")
            self.last_name = user.get("last_name")
        else:
            # Unknown update type, set defaults
            self.type = "unknown"
            self.chat = None
            self.text = ""
            self.command = ""
            self.args = ""
            self.message_id = None
            self.user_id = None
            self.username = None
            self.first_name = None
            self.last_name = None

    def get_voice_file_id(self) -> Optional[str]:
        """Get file_id for voice messages, or None if not a voice message."""
        if self.type == "voice":
            return self.raw["message"]["voice"]["file_id"]
        return None

    def get_audio_file_id(self) -> Optional[str]:
        """Get file_id for audio messages, or None if not an audio message."""
        if self.type == "audio":
            return self.raw["message"]["audio"]["file_id"]
        return None


SplitterFn = Callable[[str, int], Tuple[str, int]]
"""Return (visible_part, cut_pos) where cut_pos is the byte index **after** the split.
visible_part may differ from buffer[:cut_pos] (e.g. you replaced a space with …)."""


def inline_keyboard(buttons: list[list[tuple[str, str]]]) -> dict:
    """
    Create an inline keyboard markup.

    Args:
        buttons: List of rows, where each row is a list of (text, callback_data) tuples

    Returns:
        Dictionary suitable for reply_markup parameter

    Example:
        keyboard = inline_keyboard([
            [("Yes", "confirm_yes"), ("No", "confirm_no")],
            [("Cancel", "cancel")]
        ])
        bot.send(chat_id, "Confirm?", reply_markup=keyboard)
    """
    return {
        "inline_keyboard": [
            [{"text": text, "callback_data": data} for text, data in row]
            for row in buttons
        ]
    }


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
                 skip_history: bool = True, offset_file: Optional[str] = None,
                 auth_gate: Optional[Callable[[Event], Tuple[bool, Optional[str]]]] = None):
        self.token = token
        self.url = f"https://api.telegram.org/bot{token}/"
        self._sess = requests.Session()
        self._cmds = commands
        self._history_skipped = False
        self._auth_gate = auth_gate

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
              skip_history: bool = True, offset_file: Optional[str] = None,
              auth_gate: Optional[Callable[[Event], Tuple[bool, Optional[str]]]] = None) -> "TelegramBot":
        return cls(token, commands, skip_history, offset_file, auth_gate)

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
                        ev = Event(u)
                        if self._auth_gate is not None:
                            try:
                                ok, msg = self._auth_gate(ev)
                            except Exception as e:
                                logger.warning("auth_gate error: %s", e)
                                ok, msg = False, ""
                            if not ok:
                                if msg:
                                    try:
                                        # best-effort send; ignore failures
                                        if ev.chat is not None:
                                            self.send(ev.chat, msg)
                                    except Exception:
                                        pass
                                continue
                        handler(ev)
                except Exception as e:
                    logger.exception("poll crash: %s", e)
                    time.sleep(1)

        # Run polling directly in the main thread
        try:
            poll()
        except KeyboardInterrupt:
            print("\nBot stopped.")

    # ---------- message sending ----------
    def send(self, chat: int, text: str, **kw) -> dict:
        """
        Send a message to a chat.

        Args:
            chat: Chat ID
            text: Message text
            **kw: Additional parameters (reply_markup, reply_to_message_id, etc.)

        Returns:
            Message object from Telegram API
        """
        return self._raw_send(chat, text, **kw)

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

    def download_file(self, file_id: str) -> bytes:
        """
        Download a file from Telegram by file_id.

        Args:
            file_id: Telegram file ID

        Returns:
            File contents as bytes
        """
        # Get file path
        file_info = self._post("getFile", {"file_id": file_id})
        if not file_info:
            raise RuntimeError(f"Failed to get file info for {file_id}")

        file_path = file_info.get("file_path")
        if not file_path:
            raise RuntimeError(f"No file_path in response for {file_id}")

        # Download file
        file_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"
        response = self._sess.get(file_url, timeout=30)
        response.raise_for_status()

        return response.content

    def edit_message_text(self, chat: int, message_id: int, text: str, **kw) -> dict:
        """
        Edit an existing message.

        Args:
            chat: Chat ID
            message_id: Message ID to edit
            text: New text
            **kw: Additional parameters (reply_markup, parse_mode, etc.)

        Returns:
            Edited message object
        """
        payload = {
            "chat_id": chat,
            "message_id": message_id,
            "text": text,
            **kw
        }
        return self._post("editMessageText", payload)

    def delete_message(self, chat: int, message_id: int) -> bool:
        """
        Delete a message.

        Args:
            chat: Chat ID
            message_id: Message ID to delete

        Returns:
            True if successful
        """
        payload = {
            "chat_id": chat,
            "message_id": message_id
        }
        result = self._post("deleteMessage", payload)
        return result is not None

    def answer_callback_query(self, callback_query_id: str, text: Optional[str] = None,
                              show_alert: bool = False) -> bool:
        """
        Answer a callback query from an inline button.

        Args:
            callback_query_id: ID from callback_query update
            text: Optional notification text to show user
            show_alert: If True, show alert instead of notification

        Returns:
            True if successful

        Example:
            # In event handler for callback_query:
            bot.answer_callback_query(
                ev.raw["callback_query"]["id"],
                text="Action confirmed!"
            )
        """
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        if show_alert:
            payload["show_alert"] = True

        result = self._post("answerCallbackQuery", payload)
        return result is not None

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
        return self._post("sendMessage", {"chat_id": chat, "text": text, **kw})

    def register_commands(self, table: list) -> None:
        # Log registered commands for visibility
        try:
            names = [c.name for c in table]
            msg = f"registering commands: {names}"
            if _DEBUG:
                print(f"[telegram_mini] {msg}")
            else:
                logger.info(msg)
        except Exception:
            pass
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
