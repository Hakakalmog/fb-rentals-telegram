#!/usr/bin/env python3
"""Test script for Facebook scraping without LLM filtering.

This script will scrape posts from configured groups and display the raw results.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from dotenv import load_dotenv  # noqa: E402

from scraper import scrape_facebook_groups  # noqa: E402

# Load environment variables
load_dotenv()


def setup_logging():
  """Set up logging for the test script."""
  logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
  )


def format_post_output(post: dict) -> str:
  """Format a post for readable output."""
  separator = "=" * 80
  return f"""
{separator}
POST ID: {post.get('post_id', 'N/A')}
AUTHOR: {post.get('author', 'N/A')}
TIMESTAMP: {post.get('timestamp', 'N/A')}
GROUP: {post.get('group_url', 'N/A')}

CONTENT:
{post.get('content', 'N/A')}

LINK: {post.get('link', 'N/A')}
{separator}
"""


def save_results_to_file(posts: list, filename: str = None):
  """Save scraping results to a JSON file."""
  if not filename:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"scraped_posts_{timestamp}.json"

  with open(filename, "w", encoding="utf-8") as f:
    json.dump(posts, f, indent=2, ensure_ascii=False, default=str)

  print(f"\n📁 Results saved to: {filename}")


async def main():
  """Main function to test Facebook scraping."""
  setup_logging()

  print("🤖 Facebook Scraper Test (Without LLM)")
  print("=" * 50)

  # Get configuration from environment
  group_urls_str = os.getenv("FB_GROUP_URLS")
  if not group_urls_str:
    print("❌ Error: FB_GROUP_URLS not found in .env file")
    print("Please set FB_GROUP_URLS in your .env file with comma-separated URLs")
    return

  group_urls = [url.strip() for url in group_urls_str.split(",")]
  max_posts = int(os.getenv("MAX_POSTS_PER_SCRAPE", "10"))
  headless = os.getenv("HEADLESS_MODE", "true").lower() == "true"

  print(f"📍 Groups to scrape: {len(group_urls)}")
  for i, url in enumerate(group_urls, 1):
    print(f"   {i}. {url}")
  print(f"📊 Max posts per group: {max_posts}")
  print(f"🖥️  Headless mode: {headless}")
  print()

  # Ask user if they want to proceed
  try:
    response = input("Continue with scraping? (y/N): ").lower().strip()
    if response not in ["y", "yes"]:
      print("❌ Scraping cancelled by user")
      return
  except KeyboardInterrupt:
    print("\n❌ Scraping cancelled by user")
    return

  print("\n🚀 Starting scraping process...")
  print("⏳ This may take a few minutes...")

  try:
    # Scrape the posts
    posts = await scrape_facebook_groups(
      group_urls=group_urls, max_posts_per_group=max_posts, headless=headless
    )

    print("\n✅ Scraping completed!")
    print(f"📈 Total posts found: {len(posts)}")

    if not posts:
      print("⚠️  No posts were scraped. This could mean:")
      print("   - You're not logged into Facebook")
      print("   - The groups are private/inaccessible")
      print("   - The group URLs are invalid")
      print("   - Rate limiting or anti-bot measures")
      return

    # Display results
    print("\n" + "=" * 80)
    print("SCRAPED POSTS SUMMARY")
    print("=" * 80)

    for i, post in enumerate(posts, 1):
      print(f"\n[POST {i}/{len(posts)}]")
      print(format_post_output(post))

    # Ask if user wants to save results
    try:
      save_response = (
        input(f"\nSave {len(posts)} posts to JSON file? (Y/n): ")
        .lower()
        .strip()
      )
      if save_response in ["", "y", "yes"]:
        save_results_to_file(posts)
    except KeyboardInterrupt:
      print("\n❌ Save cancelled by user")

    print("\n🎉 Test completed successfully!")

  except Exception as e:
    print(f"\n❌ Error during scraping: {e}")
    logging.error(f"Scraping error: {e}", exc_info=True)


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("\n❌ Script interrupted by user")
  except Exception as e:
    print(f"\n💥 Fatal error: {e}")
    logging.error(f"Fatal error: {e}", exc_info=True)
