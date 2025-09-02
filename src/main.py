import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any

import schedule
from dotenv import load_dotenv

from .db import DatabaseManager
from .analyzer import ApartmentAnalyzer
from .notifier import TelegramNotifier
from .scraper import scrape_facebook_groups


# Configure logging
def setup_logging(log_level: str = "INFO", log_file: str = None):
  """Set up logging configuration."""
  # Create logs directory if it doesn't exist
  if log_file:
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
      os.makedirs(log_dir, exist_ok=True)

  # Configure logging format
  formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  )

  # Set up root logger
  logger = logging.getLogger()
  logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

  # Console handler
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(formatter)
  logger.addHandler(console_handler)

  # File handler if specified
  if log_file:
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class FacebookRentalScraper:
  """Main application class for Facebook rental post scraping and notification."""

  def __init__(self):
    """Initialize the scraper with configuration and components."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "./logs/app.log")
    setup_logging(log_level, log_file)

    self.logger = logging.getLogger(__name__)

    # Initialize components
    self.db = DatabaseManager(os.getenv("DATABASE_PATH", "./data/posts.db"))

    # Facebook groups to scrape
    fb_groups = os.getenv("FB_GROUP_URLS", "").strip()
    self.group_urls = [url.strip() for url in fb_groups.split(",") if url.strip()]

    self.analyzer = ApartmentAnalyzer()

    # Telegram notifier
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not telegram_token or not telegram_chat_id:
      self.logger.error(
        "Telegram configuration missing. Please set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
      )
      raise ValueError("Telegram configuration required")

    self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)

    # Scraping configuration
    self.max_posts_per_scrape = int(os.getenv("MAX_POSTS_PER_SCRAPE", 50))
    self.scrape_interval = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 30))
    self.headless_mode = os.getenv("HEADLESS_MODE", "false").lower() == "true"

    self.logger.info("Facebook Rental Scraper initialized")
    self.logger.info(f"Monitoring {len(self.group_urls)} groups")
    self.logger.info(f"Scrape interval: {self.scrape_interval} minutes")

  async def validate_configuration(self) -> bool:
    """Validate that all required components are working."""
    self.logger.info("Validating configuration...")

    # Check if we have groups to monitor
    if not self.group_urls:
      self.logger.error("No Facebook group URLs configured")
      return False

    # Test Telegram connection
    try:
      if not await self.notifier.test_connection():
        self.logger.error("Telegram connection failed")
        return False
    except Exception as e:
      self.logger.error(f"Telegram test failed: {e}")
      return False

    # Test database
    try:
      post_count = self.db.get_post_count()
      self.logger.info(f"Database connection OK. Current posts: {post_count}")
    except Exception as e:
      self.logger.error(f"Database connection failed: {e}")
      return False

    # Test Ollama connection (optional)
    if self.analyzer.test_ollama_connection():
      self.logger.info("Ollama connection successful")
    else:
      self.logger.warning("Ollama not available, analyzer may fail")

    self.logger.info("Configuration validation completed")
    return True

  async def scrape_and_filter_posts(self) -> list[dict[str, Any]]:
    """Scrape posts from Facebook groups and filter them."""
    self.logger.info("Starting post scraping...")

    try:
      # Scrape posts from all groups
      all_posts = await scrape_facebook_groups(
        group_urls=self.group_urls,
        max_posts_per_group=self.max_posts_per_scrape,
        headless=self.headless_mode,
      )

      if not all_posts:
        self.logger.warning("No posts scraped from any groups")
        return []

      self.logger.info(
        f"Scraped {len(all_posts)} posts from {len(self.group_urls)} groups"
      )

      # Filter out posts we've already seen
      new_posts = []
      for post in all_posts:
        if not self.db.post_exists(post["id"]):
          new_posts.append(post)

      self.logger.info(
        f"Found {len(new_posts)} new posts (filtered out {len(all_posts) - len(new_posts)} duplicates)"
      )

      if not new_posts:
        return []

      # Filter posts using LLM
      relevant_posts = self.analyzer.filter_posts(new_posts)

      self.logger.info(f"Filtered to {len(relevant_posts)} relevant posts")

      return relevant_posts

    except Exception as e:
      self.logger.error(f"Error during scraping and filtering: {e}")
      await self.notifier.send_error_notification(str(e))
      return []

  async def process_new_posts(self, posts: list[dict[str, Any]]) -> int:
    """Process and notify about new posts."""
    if not posts:
      return 0

    success_count = 0

    for post in posts:
      try:
        # Save post to database
        if self.db.save_post(post):
          # Send notification
          if await self.notifier.send_post_notification(post):
            # Mark as notified
            self.db.mark_post_notified(post["id"])
            success_count += 1
          else:
            self.logger.warning(
              f"Failed to notify about post: {post['id']}"
            )
        else:
          self.logger.error(f"Failed to save post: {post['id']}")

      except Exception as e:
        self.logger.error(
          f"Error processing post {post.get('id', 'Unknown')}: {e}"
        )

    return success_count

  async def run_scraping_cycle(self):
    """Run one complete scraping cycle."""
    start_time = datetime.now()
    self.logger.info(f"Starting scraping cycle at {start_time}")

    try:
      # Scrape and filter posts
      relevant_posts = await self.scrape_and_filter_posts()

      # Process new posts
      notified_count = await self.process_new_posts(relevant_posts)

      # Send summary
      self.db.get_post_count()

      end_time = datetime.now()
      duration = (end_time - start_time).total_seconds()

      self.logger.info(f"Scraping cycle completed in {duration:.1f} seconds")
      self.logger.info(
        f"Found {len(relevant_posts)} relevant posts, notified about {notified_count}"
      )

      # Clean up old posts periodically
      if datetime.now().hour == 2:  # Run cleanup at 2 AM
        self.db.cleanup_old_posts(30)

    except Exception as e:
      self.logger.error(f"Error in scraping cycle: {e}")
      await self.notifier.send_error_notification(f"Scraping cycle error: {e}")

  def setup_scheduler(self):
    """Set up the scraping schedule."""
    schedule.every(self.scrape_interval).minutes.do(
      lambda: asyncio.create_task(self.run_scraping_cycle())
    )

    self.logger.info(
      f"Scheduler set up to run every {self.scrape_interval} minutes"
    )

  async def run_once(self):
    """Run the scraper once (for testing or manual runs)."""
    if not await self.validate_configuration():
      self.logger.error("Configuration validation failed")
      return False

    await self.run_scraping_cycle()
    return True

  async def run_continuously(self):
    """Run the scraper continuously with scheduling."""
    if not await self.validate_configuration():
      self.logger.error("Configuration validation failed")
      return

    # Send startup notification
    await self.notifier.send_test_message()

    self.logger.info("Starting continuous scraping mode...")

    # Run initial scrape
    await self.run_scraping_cycle()

    # Set up scheduler
    self.setup_scheduler()

    # Main loop
    try:
      while True:
        schedule.run_pending()
        await asyncio.sleep(60)  # Check every minute

    except KeyboardInterrupt:
      self.logger.info("Shutting down scraper...")
    except Exception as e:
      self.logger.error(f"Unexpected error in main loop: {e}")
      await self.notifier.send_error_notification(f"Scraper crashed: {e}")


async def main():
  """Main entry point."""
  import sys

  scraper = FacebookRentalScraper()

  if len(sys.argv) > 1:
    command = sys.argv[1].lower()

    if command == "once":
      # Run once for testing
      await scraper.run_once()
    elif command == "test":
      # Test configuration
      if await scraper.validate_configuration():
        print("✅ Configuration is valid")
        await scraper.notifier.send_test_message()
      else:
        print("❌ Configuration validation failed")
        sys.exit(1)
    elif command == "continuous":
      # Run continuously
      await scraper.run_continuously()
    else:
      print("Usage: python main.py [once|test|continuous]")
      print("  once: Run scraper once and exit")
      print("  test: Test configuration and send test message")
      print("  continuous: Run scraper continuously (default)")
      sys.exit(1)
  else:
    # Default: run continuously
    await scraper.run_continuously()


if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("\nShutdown requested by user")
  except Exception as e:
    print(f"Fatal error: {e}")
    logging.error(f"Fatal error: {e}")
    sys.exit(1)
