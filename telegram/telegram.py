# telegram_loop.py
from __future__ import annotations
import asyncio
from command_router import Router, Caller, command
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

class TelegramCaller(Caller):
    """Caller implementation that talks to Telegram."""
    __slots__ = ("chat_id", "context")
    def __init__(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        self.chat_id = chat_id
        self.context = context
    async def send(self, text: str) -> None:
        await self.context.bot.send_message(chat_id=self.chat_id, text=text)

class TelegramBot(Router):
    """Thin Router-based Telegram bot."""
    def __init__(self, token: str, delim: str = "/"):
        super().__init__(delim)
        self.token = token

    # ---------- internal ----------
    async def _route(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        caller = TelegramCaller(update.message.chat_id, context)
        try:
            # Router expects a sync handle(); we run it in the default executor.
            await asyncio.get_running_loop().run_in_executor(
                None, self.handle, update.message.text, caller
            )
        except KeyboardInterrupt:          # raised by /quit
            await caller.send("Good-bye.")
            # stop the entire application
            asyncio.create_task(context.application.stop())

    # ---------- public ----------
    def run(self) -> None:
        app = Application.builder().token(self.token).build()
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._route))
        app.run_polling()

# re-export decorator so user code stays identical
from command_router import command
__all__ = ["TelegramBot", "command"]
