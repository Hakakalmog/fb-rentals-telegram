#!/usr/bin/env python3
"""Simple test to verify Telegram notifier functionality."""

import asyncio
import os
import sys

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from notifier import TelegramNotifier


async def test_telegram_notifier():
    """Test that the Telegram notifier can send a message."""
    print("🔔 Testing Telegram Notifier")
    print("=" * 40)

    # Get configuration from environment
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    # Check configuration
    if not bot_token:
        print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
        return False

    if not chat_id or chat_id == "your_chat_id_here":
        print("❌ TELEGRAM_CHAT_ID not configured in .env file")
        print("💡 Update TELEGRAM_CHAT_ID in .env with your actual chat ID")
        print()
        print("📋 What this test would do with proper configuration:")
        print("   1. Initialize TelegramNotifier")
        print("   2. Test connection to Telegram API")
        print("   3. Send a simple test message")
        print("   4. Confirm message delivery")
        return False

    print(f"🤖 Bot token: {bot_token[:10]}...")
    print(f"💬 Chat ID: {chat_id}")

    try:
        # Initialize notifier
        notifier = TelegramNotifier(bot_token, chat_id)
        print("✅ TelegramNotifier initialized")

        # Test connection
        print("🔌 Testing connection...")
        connection_ok = await notifier.test_connection()

        if not connection_ok:
            print("❌ Connection test failed")
            return False

        print("✅ Connection successful")

        # Send test message
        print("📤 Sending test message...")
        success = await notifier.send_test_message()

        if not success:
            print("❌ Test message sending failed")
            return False

        print("✅ Test message sent successfully!")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(test_telegram_notifier())
        if success:
            print("\n🎉 Telegram notifier test PASSED!")
            print("📱 Check your Telegram for the test message")
        else:
            print("\n❌ Telegram notifier test FAILED!")
            print("💡 Check your .env configuration")
    except KeyboardInterrupt:
        print("\n❌ Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
