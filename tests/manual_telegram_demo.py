#!/usr/bin/env python3
"""Interactive scraper test with Telegram demo (shows messages without sending)."""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from scraper import FacebookScraper
from notifier import TelegramNotifier

# Load environment variables from .env file
load_dotenv()


def setup_logging():
  """Set up basic logging."""
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
  )


def get_telegram_credentials():
  """Get Telegram credentials from environment."""
  bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID", "demo_chat_id")
  
  print(f"🤖 Bot Token loaded: {bot_token[:10]}...{bot_token[-10:] if bot_token else 'None'}")
  print(f"💬 Chat ID: {chat_id}")
  
  return bot_token, chat_id


class DemoTelegramNotifier:
  """Demo version that shows messages without sending them."""
  
  def __init__(self, bot_token: str, chat_id: str):
    self.bot_token = bot_token
    self.chat_id = chat_id
    self.notifier = TelegramNotifier(bot_token, chat_id)
  
  async def test_connection(self):
    """Demo connection test."""
    print("📡 [DEMO] Would test connection to Telegram API...")
    return True
  
  async def send_posts(self, posts):
    """Demo send posts function."""
    print(f"📤 [DEMO] Would send {len(posts)} posts to Telegram")
    print("=" * 60)
    
    for i, post in enumerate(posts, 1):
      # Format message using the real notifier's method
      message = self.notifier.format_post_message(post)
      
      print(f"\n📱 [MESSAGE {i}/{len(posts)}]")
      print("🎯 Chat ID:", self.chat_id)
      print("📝 Message content:")
      print("-" * 40)
      print(message)
      print("-" * 40)
      print("✅ [DEMO] Message would be sent successfully")
    
    print(f"\n🎉 [DEMO] All {len(posts)} messages would be sent to Telegram!")


async def manual_telegram_demo():
  """Test scraper with demo Telegram messaging."""
  setup_logging()

  print("🤖 Facebook Scraper + Telegram DEMO Test")
  print("=" * 50)
  print("📋 This demo shows what would be sent to Telegram")
  print("    without actually sending messages")
  print()

  # Get group URL from user
  print("Enter a Facebook group URL to test:")
  print("Example: https://www.facebook.com/groups/123456789")

  try:
    group_url = input("Group URL: ").strip()
    if not group_url:
      print("❌ No URL provided")
      return

    if "facebook.com/groups/" not in group_url:
      print("⚠️  Warning: This doesn't look like a Facebook group URL")

    max_posts = input("Max posts to scrape (default 3): ").strip() or "3"
    try:
      max_posts = int(max_posts)
    except ValueError:
      max_posts = 3

  except KeyboardInterrupt:
    print("\n❌ Cancelled by user")
    return

  print(f"\n🎯 Testing scraper on: {group_url}")
  print(f"📊 Max posts: {max_posts}")
  print("🖥️  Running in VISIBLE mode for login")

  # Get Telegram credentials
  bot_token, chat_id = get_telegram_credentials()
  if not bot_token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
    return

  print("\n📱 Initializing demo Telegram notifier...")
  demo_notifier = DemoTelegramNotifier(bot_token, chat_id)

  # Test connection (demo)
  if await demo_notifier.test_connection():
    print("✅ [DEMO] Telegram connection would work")
  else:
    print("❌ [DEMO] Telegram connection would fail")
    return

  print("\n🚀 Starting browser...")

  try:
    # Create scraper instance
    async with FacebookScraper(headless=False) as scraper:
      await scraper.initialize_browser()
      
      # Navigate to Facebook immediately so user sees the login page
      print("🌐 Navigating to Facebook login page...")
      await scraper.page.goto("https://www.facebook.com", timeout=30000)

      # Give user time to log in
      print("\n" + "="*60)
      print("🔑 MANUAL LOGIN REQUIRED")
      print("="*60)
      print("1. A Chrome browser window should have opened")
      print("2. Please log into Facebook manually")
      print("3. You can stay on any Facebook page - the script will navigate")
      print("   to your specified group automatically")
      print("4. Press ENTER here when you're logged in")
      print("="*60)

      try:
        input("Press ENTER when logged in and ready to scrape...")
      except KeyboardInterrupt:
        print("\n❌ Test cancelled")
        return

      print("\n🔄 Testing login status...")

      # Check if we're logged in by going to Facebook homepage first
      try:
        print("🌐 Checking Facebook login status...")
        await scraper.page.goto("https://www.facebook.com", timeout=30000)
        await scraper.page.wait_for_timeout(3000)  # Wait 3 seconds

        # Check current URL
        current_url = scraper.page.url
        print(f"Current page: {current_url}")

        # If we're on facebook.com (not login page), we're likely logged in
        if "facebook.com" in current_url and "login" not in current_url.lower():
          print("✅ Appears to be logged in! Scraper will navigate to group automatically.")
          is_logged_in = True
        else:
          print("❌ Still on login page or redirected away from Facebook")
          is_logged_in = False

      except Exception as e:
        print(f"⚠️  Could not verify login status: {e}")
        # Ask user if they want to continue anyway
        continue_anyway = input("Continue with scraping anyway? (y/N): ").strip().lower()
        if continue_anyway != 'y':
          return
        is_logged_in = True

      if not is_logged_in:
        print("❌ Not logged in. Please try again.")
        return

      print(f"\n📊 Now scraping {max_posts} posts from the group...")

      # Scrape the posts
      posts = await scraper.scrape_group_posts(group_url, max_posts)

      print("\n🎉 Scraping completed!")
      print(f"📈 Total posts found: {len(posts)}")

      if not posts:
        print("⚠️  No posts were scraped. This could mean:")
        print("   - The group is private/inaccessible")
        print("   - The group URL is invalid")
        print("   - The group has no recent posts")
        print("   - Rate limiting or anti-bot measures")
        return

      # Display results
      print("\n" + "="*60)
      print("SCRAPED POSTS")
      print("="*60)

      for i, post in enumerate(posts, 1):
        print(f"\n[POST {i}/{len(posts)}]")
        print(f"Author: {post.get('author', 'N/A')}")
        print(f"Content: {post.get('content', 'N/A')[:200]}{'...' if len(post.get('content', '')) > 200 else ''}")
        print(f"URL: {post.get('url', 'N/A')}")
        print("-" * 40)

      # Send to Telegram (demo)
      print("\n" + "="*60)
      print("TELEGRAM DEMO OUTPUT")
      print("="*60)
      await demo_notifier.send_posts(posts)

  except Exception as e:
    print(f"❌ Error: {e}")
    logging.error(f"Scraping failed: {e}")


if __name__ == "__main__":
  try:
    asyncio.run(manual_telegram_demo())
  except KeyboardInterrupt:
    print("\n❌ Test interrupted")
  except Exception as e:
    print(f"💥 Fatal error: {e}")
    logging.error(f"Fatal error: {e}")
