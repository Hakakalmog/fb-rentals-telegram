#!/usr/bin/env python3
"""Interactive scraper test with manual login support."""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src directory to Python path
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, "..", "src")
sys.path.insert(0, os.path.abspath(src_dir))

try:
  from scraper import FacebookScraper
except ImportError as e:
  print(f"Import error: {e}")
  print(f"Current dir: {current_dir}")
  print(f"Src dir: {src_dir}")
  print(f"Absolute src dir: {os.path.abspath(src_dir)}")
  sys.exit(1)


def setup_logging():
  """Set up basic logging."""
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
  )


async def manual_login_test():
  """Test scraper with manual login step."""
  setup_logging()

  print("🤖 Facebook Scraper - Manual Login Test")
  print("=" * 50)

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
  print("\n🚀 Starting browser...")

  try:
    # Create scraper instance
    async with FacebookScraper(headless=False) as scraper:
      await scraper.initialize_browser()

      # Give user time to log in
      print("\n" + "="*60)
      print("🔑 MANUAL LOGIN REQUIRED")
      print("="*60)
      print("1. A Chrome browser window should have opened")
      print("2. Please log into Facebook manually")
      print("3. Navigate to the group or just stay on any Facebook page")
      print("4. Press ENTER here when you're logged in")
      print("="*60)

      try:
        input("Press ENTER when logged in and ready to scrape...")
      except KeyboardInterrupt:
        print("\n❌ Test cancelled")
        return

      print("\n🔄 Testing login status...")

      # Try login check with longer timeout
      try:
        # Just navigate to Facebook main page first
        await scraper.page.goto("https://www.facebook.com", timeout=30000)
        await scraper.page.wait_for_timeout(2000)  # Wait 2 seconds

        # Check current URL
        current_url = scraper.page.url
        print(f"Current page: {current_url}")

        # If we're on facebook.com (not login page), we're likely logged in
        if "facebook.com" in current_url and "login" not in current_url.lower():
          print("✅ Appears to be logged in!")
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
      print("APARTMENT POSTS FOUND")
      print("="*60)

      for i, post in enumerate(posts, 1):
        print(f"\n[POST {i}/{len(posts)}]")
        print(f"Author: {post.get('author', 'N/A')}")
        print(f"Time: {post.get('timestamp', 'N/A')}")
        print(f"Content: {post.get('content', 'N/A')[:200]}{'...' if len(post.get('content', '')) > 200 else ''}")
        print(f"Link: {post.get('link', 'N/A')}")
        print("-" * 40)

      # Ask to save results
      save = input(f"\n💾 Save {len(posts)} posts to JSON file? (y/N): ").strip().lower()
      if save == 'y':
        # Create test_outputs directory if it doesn't exist
        test_outputs_dir = os.path.join(os.path.dirname(__file__), "..", "test_outputs")
        os.makedirs(test_outputs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scraped_apartments_{timestamp}.json"
        filepath = os.path.join(test_outputs_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as f:
          json.dump(posts, f, indent=2, ensure_ascii=False, default=str)
        print(f"✅ Results saved to test_outputs/{filename}")

  except Exception as e:
    print(f"❌ Error: {e}")
    logging.error(f"Scraping failed: {e}")


if __name__ == "__main__":
  try:
    asyncio.run(manual_login_test())
  except KeyboardInterrupt:
    print("\n❌ Test interrupted")
  except Exception as e:
    print(f"💥 Fatal error: {e}")
    logging.error(f"Fatal error: {e}")
