#!/usr/bin/env python3
"""
Example: Using inline keyboards with telegram_mini

Shows how to:
- Create inline keyboards with buttons
- Handle callback queries from button clicks
- Edit messages after button clicks
- Access user information
"""
import os
from telegram_mini import TelegramBot, Event, inline_keyboard


def main():
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        print("Set TG_BOT_TOKEN environment variable")
        return

    bot = TelegramBot.start(token=token)

    def handle_event(ev: Event):
        # Show user information
        user_info = f"User: {ev.first_name}"
        if ev.username:
            user_info += f" (@{ev.username})"
        print(f"{user_info} - Type: {ev.type}")

        if ev.type == "command" and ev.command == "start":
            # Create inline keyboard with buttons
            keyboard = inline_keyboard([
                [("✅ Yes", "action_yes"), ("❌ No", "action_no")],
                [("ℹ️ Help", "action_help")]
            ])

            bot.send(
                ev.chat,
                "Choose an option:",
                reply_markup=keyboard
            )

        elif ev.type == "callback_query":
            # Handle button clicks
            callback_id = ev.raw["callback_query"]["id"]
            action = ev.text  # callback_data

            if action == "action_yes":
                # Answer the callback query (removes loading state)
                bot.answer_callback_query(callback_id, text="You chose Yes!")

                # Edit the message to show choice
                bot.edit_message_text(
                    ev.chat,
                    ev.message_id,
                    "✅ You selected: Yes"
                )

            elif action == "action_no":
                bot.answer_callback_query(callback_id, text="You chose No!")
                bot.edit_message_text(
                    ev.chat,
                    ev.message_id,
                    "❌ You selected: No"
                )

            elif action == "action_help":
                bot.answer_callback_query(callback_id)
                bot.send(ev.chat, "This is a demo of inline keyboards!")

        elif ev.type == "text":
            # Reply to messages
            msg = bot.send(
                ev.chat,
                f"You said: {ev.text}",
                reply_to_message_id=ev.message_id
            )

            # Example: Delete message after 5 seconds
            # import time
            # time.sleep(5)
            # bot.delete_message(ev.chat, msg["message_id"])

    print("Bot starting... Send /start to see inline keyboard")
    bot.run(handle_event)


if __name__ == "__main__":
    main()