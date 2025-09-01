#!/usr/bin/env python3
"""Interactive scraper test with manual login and Telegram messaging."""

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
  """Get Telegram credentials from user or environment."""
  bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID")
  
  if not bot_token:
    print("\n🤖 Telegram Bot Configuration")
    print("=" * 40)
    bot_token = input("Enter your Telegram Bot Token: ").strip()
    
  if not chat_id:
    chat_id = input("Enter your Telegram Chat ID: ").strip()
    
  if not bot_token or not chat_id:
    print("❌ Telegram credentials are required!")
    return None, None
    
  return bot_token, chat_id


async def manual_telegram_test():
  """Test scraper with manual login and send results to Telegram."""
  setup_logging()

  print("🤖 Facebook Scraper + Telegram Test")
  print("=" * 50)

  # Get Telegram credentials
  bot_token, chat_id = get_telegram_credentials()
  if not bot_token or not chat_id:
    return

  # Get group URL from user
  print("\nEnter a Facebook group URL to test:")
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

  # Initialize Telegram notifier
  print("\n📱 Initializing Telegram bot...")
  notifier = TelegramNotifier(bot_token, chat_id)

  # Test Telegram connection
  try:
    if await notifier.test_connection():
      print("✅ Telegram bot connected successfully!")
      # Send test message
      await notifier.send_test_message()
    else:
      print("❌ Failed to connect to Telegram bot")
      return
  except Exception as e:
    print(f"❌ Telegram connection error: {e}")
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
        
        # Send error notification to Telegram
        await notifier.send_error_notification(f"No posts found in group: {group_url}")
        return

      # Display results
      print("\n" + "="*60)
      print("SCRAPED POSTS")
      print("="*60)

      for i, post in enumerate(posts, 1):
        print(f"\n[POST {i}/{len(posts)}]")
        print(f"Author: {post.get('author', 'N/A')}")
        print(f"Time: {post.get('timestamp', 'N/A')}")
        print(f"Content: {post.get('content', 'N/A')[:200]}{'...' if len(post.get('content', '')) > 200 else ''}")
        print(f"URL: {post.get('url', 'N/A')}")
        print("-" * 40)

      # Send posts to Telegram
      print(f"\n📱 Sending {len(posts)} posts to Telegram...")
      
      try:
        success_count = await notifier.notify_posts(posts)
        print(f"✅ Successfully sent {success_count}/{len(posts)} posts to Telegram!")
        
        # Send summary
        await notifier.send_summary_notification(len(posts), len(posts))
        
      except Exception as e:
        print(f"❌ Error sending to Telegram: {e}")
        await notifier.send_error_notification(f"Error sending posts: {str(e)}")

  except Exception as e:
    print(f"❌ Error: {e}")
    logging.error(f"Scraping failed: {e}")
    
    # Send error to Telegram if notifier is available
    try:
      await notifier.send_error_notification(f"Scraping failed: {str(e)}")
    except:
      pass


if __name__ == "__main__":
  try:
    asyncio.run(manual_telegram_test())
  except KeyboardInterrupt:
    print("\n❌ Test interrupted")
  except Exception as e:
    print(f"💥 Fatal error: {e}")
    logging.error(f"Fatal error: {e}")
