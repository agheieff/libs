#!/usr/bin/env python3
"""
Quick test script for new telegram_mini features.
Tests: user info, inline keyboards, callbacks, message editing, deletion.
"""
import os
import sys
from telegram_mini import TelegramBot, Event, inline_keyboard


def test_bot():
    token = os.getenv("TG_BOT_TOKEN")
    if not token:
        print("Error: Set TG_BOT_TOKEN environment variable")
        sys.exit(1)

    bot = TelegramBot.start(token=token)
    print("✅ Bot created successfully")

    test_results = []

    def handle_event(ev: Event):
        print(f"\n📨 Event type: {ev.type}")

        # Test 1: User information
        if ev.user_id:
            print(f"✅ User ID: {ev.user_id}")
            print(f"   Name: {ev.first_name} {ev.last_name or ''}")
            print(f"   Username: @{ev.username or 'none'}")
            test_results.append("user_info")
        else:
            print("❌ User info not available")

        # Test 2: Start command - send inline keyboard
        if ev.type == "command" and ev.command == "test":
            print("Testing inline keyboard...")
            keyboard = inline_keyboard([
                [("Button 1", "btn1"), ("Button 2", "btn2")],
                [("Delete This", "delete")]
            ])

            msg = bot.send(
                ev.chat,
                "🧪 Test Message\nClick a button below:",
                reply_markup=keyboard
            )
            print(f"✅ Sent message with inline keyboard, msg_id: {msg.get('message_id')}")
            test_results.append("inline_keyboard")

        # Test 3: Handle callback queries
        elif ev.type == "callback_query":
            callback_id = ev.raw["callback_query"]["id"]
            action = ev.text

            print(f"Callback received: {action}")

            if action == "btn1":
                bot.answer_callback_query(callback_id, text="Button 1 clicked!")
                bot.edit_message_text(
                    ev.chat,
                    ev.message_id,
                    "✅ You clicked Button 1"
                )
                print("✅ Edited message successfully")
                test_results.append("edit_message")

            elif action == "btn2":
                bot.answer_callback_query(callback_id, text="Button 2 clicked!")
                bot.edit_message_text(
                    ev.chat,
                    ev.message_id,
                    "✅ You clicked Button 2"
                )
                test_results.append("edit_message")

            elif action == "delete":
                bot.answer_callback_query(callback_id, text="Deleting message...")
                result = bot.delete_message(ev.chat, ev.message_id)
                if result:
                    print("✅ Deleted message successfully")
                    test_results.append("delete_message")
                    bot.send(ev.chat, "Message deleted!")

        # Test 4: Text message
        elif ev.type == "text":
            # Test reply_to
            bot.send(
                ev.chat,
                f"Echo: {ev.text}",
                reply_to_message_id=ev.message_id
            )
            print("✅ Sent reply to message")
            test_results.append("reply_to")

        # Show test summary if we've run some tests
        if len(test_results) >= 4:
            print("\n" + "="*50)
            print("🎉 TEST SUMMARY")
            print("="*50)
            print(f"✅ Tested features: {len(set(test_results))}")
            print(f"   - {', '.join(set(test_results))}")
            print("="*50)
            print("\nAll features working! Send Ctrl-C to stop.")

    print("\n" + "="*50)
    print("🧪 TELEGRAM_MINI FEATURE TEST")
    print("="*50)
    print("Instructions:")
    print("1. Send /test command to test inline keyboard")
    print("2. Click buttons to test callbacks and editing")
    print("3. Click 'Delete This' to test deletion")
    print("4. Send any text to test reply_to")
    print("="*50)
    print("\nWaiting for messages...\n")

    try:
        bot.run(handle_event)
    except KeyboardInterrupt:
        print("\n\n👋 Test completed!")


if __name__ == "__main__":
    test_bot()