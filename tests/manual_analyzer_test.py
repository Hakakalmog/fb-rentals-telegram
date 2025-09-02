#!/usr/bin/env python3
"""Test the apartment analyzer with manual scraping and Ollama analysis."""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from scraper import FacebookScraper
from analyzer import ApartmentAnalyzer
from notifier import TelegramNotifier

# Load environment variables from .env file
load_dotenv()


def setup_logging():
  """Set up basic logging."""
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
  )


class DemoAnalyzerTelegramNotifier:
  """Demo version that shows analyzed messages without sending them."""
  
  def __init__(self, bot_token: str, chat_id: str):
    self.bot_token = bot_token
    self.chat_id = chat_id
    self.notifier = TelegramNotifier(bot_token, chat_id)
  
  async def send_analyzed_posts(self, posts):
    """Demo send posts function with analysis results."""
    print(f"📤 [DEMO] Would send {len(posts)} analyzed posts to Telegram")
    print("=" * 60)
    
    # Group posts by match level
    match_groups = {
        'very high match': [],
        'high match': [],
        'low match': [],
        'very low match': []
    }
    
    for post in posts:
        match_level = post.get('match_level', 'very low match')
        match_groups[match_level].append(post)
    
    # Show summary
    print("\n🎯 ANALYSIS SUMMARY:")
    print(f"🔥 Very High Match: {len(match_groups['very high match'])} posts")
    print(f"✅ High Match: {len(match_groups['high match'])} posts")
    print(f"⚠️  Low Match: {len(match_groups['low match'])} posts")
    print(f"❌ Very Low Match: {len(match_groups['very low match'])} posts")
    
    # Show only high and very high matches
    worthy_posts = match_groups['very high match'] + match_groups['high match']
    
    if not worthy_posts:
        print("\n😔 No high-match posts found to send to Telegram")
        return
    
    print(f"\n📱 Would send {len(worthy_posts)} HIGH-MATCH posts to Telegram:")
    print("=" * 60)
    
    for i, post in enumerate(worthy_posts, 1):
      # Format message using the real notifier's method
      message = self.notifier.format_post_message(post)
      match_level = post.get('match_level', 'unknown')
      
      # Add match level indicator
      match_emoji = {
          'very high match': '🔥🏆',
          'high match': '✅',
          'low match': '⚠️',
          'very low match': '❌'
      }.get(match_level, '❓')
      
      print(f"\n📱 [MESSAGE {i}/{len(worthy_posts)}] {match_emoji} {match_level.upper()}")
      print("🎯 Chat ID:", self.chat_id)
      print("📝 Message content:")
      print("-" * 40)
      print(message)
      print("-" * 40)
      print("✅ [DEMO] High-match message would be sent successfully")
    
    print(f"\n🎉 [DEMO] {len(worthy_posts)} high-match messages would be sent to Telegram!")


async def manual_analyzer_test():
  """Test scraper with Ollama analysis and demo Telegram messaging."""
  setup_logging()

  print("🤖 Facebook Scraper + Ollama Analyzer + Telegram DEMO")
  print("=" * 55)
  print("📋 This demo scrapes posts, analyzes them with Ollama LLM,")
  print("    and shows what high-match posts would be sent to Telegram")
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

    max_posts = input("Max posts to scrape (default 5): ").strip() or "5"
    try:
      max_posts = int(max_posts)
    except ValueError:
      max_posts = 5

  except KeyboardInterrupt:
    print("\n❌ Cancelled by user")
    return

  print(f"\n🎯 Testing on: {group_url}")
  print(f"📊 Max posts: {max_posts}")
  print("🖥️  Running in VISIBLE mode for login")

  # Initialize Ollama analyzer
  print("\n🧠 Initializing Ollama analyzer...")
  model_name = os.getenv("OLLAMA_MODEL")
  if not model_name:
    print("❌ OLLAMA_MODEL environment variable is required")
    return
  ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
  
  analyzer = ApartmentAnalyzer(model_name=model_name, ollama_host=ollama_host)
  
  # Test Ollama connection
  if not analyzer.test_ollama_connection():
    print("❌ Cannot connect to Ollama. Make sure it's running:")
    print("   ollama serve")
    print(f"   ollama pull {model_name}")
    return

  # Get Telegram credentials
  bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
  chat_id = os.getenv("TELEGRAM_CHAT_ID", "demo_chat_id")
  
  if not bot_token:
    print("❌ TELEGRAM_BOT_TOKEN not found in .env file")
    return

  print("\n📱 Initializing demo Telegram notifier...")
  demo_notifier = DemoAnalyzerTelegramNotifier(bot_token, chat_id)

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

      # Check if we're logged in
      try:
        print("🌐 Checking Facebook login status...")
        await scraper.page.goto("https://www.facebook.com", timeout=30000)
        await scraper.page.wait_for_timeout(3000)

        current_url = scraper.page.url
        print(f"Current page: {current_url}")

        if "facebook.com" in current_url and "login" not in current_url.lower():
          print("✅ Appears to be logged in! Scraper will navigate to group automatically.")
          is_logged_in = True
        else:
          print("❌ Still on login page or redirected away from Facebook")
          is_logged_in = False

      except Exception as e:
        print(f"⚠️  Could not verify login status: {e}")
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
        print("⚠️  No posts were scraped.")
        return

      # Analyze posts with Ollama
      print("\n🧠 Analyzing posts with Ollama LLM...")
      print(f"🤖 Using model: {model_name}")
      print("📋 Criteria: 3+ rooms, max 5,900 ₪, prefer light rail access")
      
      analyzed_posts = await analyzer.analyze_posts(posts)

      # Display results
      print("\n" + "="*60)
      print("ANALYSIS RESULTS")
      print("="*60)

      for i, post in enumerate(analyzed_posts, 1):
        match_level = post.get('match_level', 'unknown')
        match_emoji = {
            'very high match': '🔥🏆',
            'high match': '✅',
            'low match': '⚠️',
            'very low match': '❌'
        }.get(match_level, '❓')
        
        print(f"\n[POST {i}/{len(analyzed_posts)}] {match_emoji} {match_level.upper()}")
        print(f"Author: {post.get('author', 'N/A')}")
        print(f"Content: {post.get('content', 'N/A')[:150]}{'...' if len(post.get('content', '')) > 150 else ''}")
        print("-" * 40)

      # Send high-match posts to Telegram (demo)
      print("\n" + "="*60)
      print("TELEGRAM DEMO OUTPUT")
      print("="*60)
      await demo_notifier.send_analyzed_posts(analyzed_posts)

  except Exception as e:
    print(f"❌ Error: {e}")
    logging.error(f"Test failed: {e}")


if __name__ == "__main__":
  try:
    asyncio.run(manual_analyzer_test())
  except KeyboardInterrupt:
    print("\n❌ Test interrupted")
  except Exception as e:
    print(f"💥 Fatal error: {e}")
    logging.error(f"Fatal error: {e}")
