from __future__ import annotations
import asyncio
import logging
from typing import Optional, Any
from command_router import Router, Caller, command
from telegram import Update, Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logger = logging.getLogger(__name__)

class TelegramCaller(Caller):
    def __init__(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE):
        self.chat_id = chat_id
        self.context = context
        self._pending_messages = []
    
    def send(self, text: str) -> None:
        """Queue message to be sent (sync interface for Router)"""
        self._pending_messages.append(text)
    
    def reply(self, text: str) -> None:
        """Alias for send - more intuitive for replies"""
        self.send(text)
    
    async def flush_messages(self) -> None:
        """Send all queued messages"""
        for text in self._pending_messages:
            try:
                await self.context.bot.send_message(chat_id=self.chat_id, text=text)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
        self._pending_messages.clear()

class TelegramBot(Router):
    
    def __init__(self, token: str, delim: str = "/"):
        super().__init__(delim)
        self.token = token
        self._app: Optional[Application] = None
        self._bot: Optional[Bot] = None
    
    # ---------- convenience methods ----------
    
    async def send_message_async(self, chat_id: int, text: str) -> None:
        """Send a message to any chat (async)"""
        if self._bot:
            try:
                await self._bot.send_message(chat_id=chat_id, text=text)
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    def get_bot(self) -> Optional[Bot]:
        """Get the underlying Bot instance"""
        return self._bot
    
    def get_app(self) -> Optional[Application]:
        """Get the underlying Application instance"""
        return self._app
    
    # ---------- internal ----------
    
    async def _route(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not update.message or not update.message.text:
            return
        
        caller = TelegramCaller(update.message.chat_id, context)
        
        try:
            # Router expects a sync handle(); we run it in the default executor
            await asyncio.get_running_loop().run_in_executor(
                None, self.handle, update.message.text, caller
            )
            # After sync processing, send all queued messages
            await caller.flush_messages()
            
        except KeyboardInterrupt:  # raised by /quit
            await context.bot.send_message(chat_id=update.message.chat_id, text="Good-bye.")
            # stop the entire application
            asyncio.create_task(context.application.stop())
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await context.bot.send_message(
                chat_id=update.message.chat_id, 
                text="Sorry, something went wrong."
            )
    
    # ---------- public ----------
    
    def run(self) -> None:
        """Start the bot with polling"""
        self._app = Application.builder().token(self.token).build()
        self._bot = self._app.bot
        
        self._app.add_handler(
            MessageHandler(filters.TEXT, self._route)
        )
        
        logger.info("Starting bot...")
        self._app.run_polling()
    
    async def run_async(self) -> None:
        """Async version of run() for integration with other async code"""
        self._app = Application.builder().token(self.token).build()
        self._bot = self._app.bot
        
        self._app.add_handler(
            MessageHandler(filters.TEXT, self._route)
        )
        
        logger.info("Starting bot (async)...")
        async with self._app:
            await self._app.start()
            await self._app.updater.start_polling()
            await asyncio.Event().wait()  # Run forever
    
    def stop(self) -> None:
        """Stop the bot gracefully"""
        if self._app:
            asyncio.create_task(self._app.stop())

# Re-export decorator so user code stays identical
from command_router import command

__all__ = ["TelegramBot", "command"]
