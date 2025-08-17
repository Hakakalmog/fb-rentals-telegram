#!/usr/bin/env python3
"""Simple scraper test - minimal configuration required.

Just provide a Facebook group URL directly.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from scraper import scrape_facebook_groups  # noqa: E402


def setup_logging():
  """Set up basic logging."""
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
  )


async def main():
  """Simple scraper test with direct URL input."""
  setup_logging()

  print("🤖 Simple Facebook Scraper Test")
  print("=" * 40)

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

    headless_input = input("Run in headless mode? (Y/n): ").strip().lower()
    headless = headless_input in ["", "y", "yes"]

  except KeyboardInterrupt:
    print("\n❌ Cancelled by user")
    return

  print(f"\n🎯 Testing scraper on: {group_url}")
  print(f"📊 Max posts: {max_posts}")
  print(f"🖥️  Headless: {headless}")
  print("\n🚀 Starting...")

  try:
    posts = await scrape_facebook_groups(
      group_urls=[group_url], max_posts_per_group=max_posts, headless=headless
    )

    print(f"\n✅ Found {len(posts)} posts")

    if posts:
      print("\n" + "=" * 60)
      print("SCRAPED POSTS")
      print("=" * 60)

      for i, post in enumerate(posts, 1):
        print(f"\n--- POST {i} ---")
        print(f"ID: {post.get('post_id', 'N/A')}")
        print(f"Author: {post.get('author', 'N/A')}")
        print(f"Time: {post.get('timestamp', 'N/A')}")
        print(
          f"Content: {post.get('content', 'N/A')[:200]}{'...' if len(post.get('content', '')) > 200 else ''}"
        )
        print(f"Link: {post.get('link', 'N/A')}")

      # Save option
      save = input("\nSave results to JSON? (y/N): ").strip().lower()
      if save == "y":
        # Create test_outputs directory if it doesn't exist
        test_outputs_dir = os.path.join(os.path.dirname(__file__), "..", "test_outputs")
        os.makedirs(test_outputs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_scrape_{timestamp}.json"
        filepath = os.path.join(test_outputs_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
          json.dump(posts, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 Saved to test_outputs/{filename}")
    else:
      print("⚠️  No posts found. Check if you're logged into Facebook.")

  except Exception as e:
    print(f"❌ Error: {e}")
    logging.error(f"Scraping failed: {e}")


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("\n❌ Interrupted")
