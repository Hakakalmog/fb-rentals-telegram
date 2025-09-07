#!/usr/bin/env python3
"""
Facebook Rental Bot - Professional Implementation

This application monitors Facebook rental groups, analyzes posts with AI,
and sends matching apartments to Telegram.

Usage:
    python main.py              # Run continuously (default)
    python main.py once         # Run once and exit
    python main.py test         # Test configuration
"""

import asyncio
import logging
import os
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv

# Import our modules
from src.db import DatabaseManager
from src.analyzer import ApartmentAnalyzer
from src.notifier import TelegramNotifier
from src.scraper import FacebookScraper


def setup_logging():
    """Setup professional logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("app.log", encoding='utf-8')
        ]
    )


class FacebookRentalBot:
    """Professional Facebook rental monitoring bot."""
    
    def __init__(self):
        """Initialize the bot with configuration."""
        # Load environment variables
        load_dotenv()
        
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger("RentalBot")
        
        # Initialize components
        self.db = DatabaseManager(os.getenv("DATABASE_PATH", "posts.db"))
        self.analyzer = ApartmentAnalyzer()
        
        # Get configuration
        self.facebook_groups = self._get_facebook_groups()
        self.max_posts_per_group = int(os.getenv("MAX_POSTS_PER_SCRAPE", "50"))
        self.scrape_interval_minutes = int(os.getenv("SCRAPE_INTERVAL_MINUTES", "10"))
        
        # Downtime configuration
        self.downtime_enabled = os.getenv("DOWNTIME_ENABLED", "false").lower() == "true"
        self.downtime_start_hour = int(os.getenv("DOWNTIME_START_HOUR", "2"))
        self.downtime_duration_hours = int(os.getenv("DOWNTIME_DURATION_HOURS", "4"))
        
        if self.downtime_enabled:
            end_hour = (self.downtime_start_hour + self.downtime_duration_hours) % 24
            self.logger.info(f"Scheduled downtime enabled: {self.downtime_start_hour:02d}:00 - {end_hour:02d}:00")
        
        # Initialize Telegram notifier
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if telegram_token and telegram_chat_id:
            self.notifier = TelegramNotifier(telegram_token, telegram_chat_id)
        else:
            self.notifier = None
            self.logger.warning("Telegram not configured - notifications disabled")
        
        self.logger.info(f"Bot initialized - monitoring {len(self.facebook_groups)} groups")
    
    def _get_facebook_groups(self) -> List[str]:
        """Get Facebook group URLs from environment."""
        fb_groups = os.getenv("FB_GROUP_URLS", "").strip()
        if not fb_groups:
            self.logger.error("No Facebook groups configured in FB_GROUP_URLS")
            return []
        
        groups = [url.strip() for url in fb_groups.split(",") if url.strip()]
        return groups
    
    def is_downtime(self) -> bool:
        """Check if current time is within scheduled downtime."""
        if not self.downtime_enabled:
            return False
        
        current_hour = datetime.now().hour
        start_hour = self.downtime_start_hour
        end_hour = (start_hour + self.downtime_duration_hours) % 24
        
        # Handle downtime that spans midnight
        if start_hour <= end_hour:
            # Normal case: e.g., 2:00-6:00 (2 <= hour < 6)
            return start_hour <= current_hour < end_hour
        else:
            # Spans midnight: e.g., 22:00-2:00 (hour >= 22 OR hour < 2)
            return current_hour >= start_hour or current_hour < end_hour

    def get_downtime_status_message(self) -> str:
        """Get a descriptive message about downtime status."""
        if not self.downtime_enabled:
            return "Downtime disabled"
        
        start_hour = self.downtime_start_hour
        end_hour = (start_hour + self.downtime_duration_hours) % 24
        
        if self.is_downtime():
            return f"🌙 In downtime until {end_hour:02d}:00"
        else:
            return f"✅ Active (downtime: {start_hour:02d}:00-{end_hour:02d}:00)"

    async def test_configuration(self) -> bool:
        """Test that all components are working."""
        self.logger.info("🔍 Testing configuration...")
        
        # Test database
        try:
            post_count = self.db.get_post_count()
            self.logger.info(f"✅ Database OK - {post_count} posts stored")
        except Exception as e:
            self.logger.error(f"❌ Database failed: {e}")
            return False
        
        # Test Ollama
        if self.analyzer.test_ollama_connection():
            self.logger.info("✅ Ollama AI connection OK")
        else:
            self.logger.error("❌ Ollama AI connection failed")
            return False
        
        # Test Telegram (optional)
        if self.notifier:
            try:
                if await self.notifier.test_connection():
                    self.logger.info("✅ Telegram connection OK")
                else:
                    self.logger.warning("⚠️  Telegram connection failed (continuing anyway)")
            except Exception as e:
                self.logger.warning(f"⚠️  Telegram test failed: {e} (continuing anyway)")
        
        # Test Facebook groups
        if not self.facebook_groups:
            self.logger.error("❌ No Facebook groups configured")
            return False

        # Show downtime configuration
        self.logger.info(f"🕐 Downtime status: {self.get_downtime_status_message()}")

        self.logger.info("✅ Configuration test completed")
        return True
    
    async def verify_facebook_login(self, scraper: FacebookScraper) -> bool:
        """Verify Facebook login using proven method from manual_login_test.py"""
        try:
            self.logger.info("🌐 Navigating to Facebook for login verification...")
            await scraper.page.goto("https://www.facebook.com", timeout=30000)
            await scraper.page.wait_for_timeout(3000)  # Wait 3 seconds like manual test
            
            # Check current URL to see if logged in (from test_configurable_scraper.py)
            current_url = scraper.page.url
            self.logger.info(f"Current page: {current_url}")
            
            # If we're on facebook.com (not login page), we're likely logged in
            if "facebook.com" in current_url and "login" not in current_url.lower():
                self.logger.info("✅ Facebook login detected!")
                return True
            else:
                self.logger.error("❌ Not logged into Facebook - please login in your browser first")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error verifying Facebook login: {e}")
            return False

    async def scrape_facebook_group(self, scraper: FacebookScraper, group_url: str) -> List[Dict[str, Any]]:
        """Scrape posts from a single Facebook group using proven method."""
        try:
            self.logger.info(f"🕷️  Scraping group: {group_url}")
            
            # Use the proven scrape_group_posts method from test_configurable_scraper.py
            posts = await scraper.scrape_group_posts(group_url, self.max_posts_per_group)
            
            self.logger.info(f"📊 Scraped {len(posts)} posts from group")
            return posts
            
        except Exception as e:
            self.logger.error(f"❌ Failed to scrape group {group_url}: {e}")
            return []

    async def scrape_all_groups(self) -> List[Dict[str, Any]]:
        """Scrape new posts from all Facebook groups using proven methods."""
        self.logger.info(f"🕷️  Starting to scrape {len(self.facebook_groups)} groups...")
        
        all_posts = []
        
        try:
            # Use the proven FacebookScraper approach from test_configurable_scraper.py
            async with FacebookScraper() as scraper:
                await scraper.initialize_browser()
                
                # Verify login using proven method
                if not await self.verify_facebook_login(scraper):
                    return []
                
                # Scrape each group
                for group_url in self.facebook_groups:
                    group_posts = await self.scrape_facebook_group(scraper, group_url)
                    # Add group_url to each post
                    for post in group_posts:
                        post["group_url"] = group_url
                    all_posts.extend(group_posts)
                    
                    # Add delay between groups to avoid rate limiting
                    if len(self.facebook_groups) > 1:
                        await asyncio.sleep(5)

            self.logger.info(f"📊 Total posts scraped: {len(all_posts)}")

            # Filter out posts we've already seen
            new_posts = []
            for post in all_posts:
                if not self.db.post_exists(post["id"]):
                    new_posts.append(post)
                    # Save new post to database
                    self.db.save_post(post)

            self.logger.info(f"🆕 Found {len(new_posts)} new posts")
            return new_posts

        except Exception as e:
            self.logger.error(f"❌ Scraping failed: {e}")
            return []
    
    def analyze_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze posts with AI to find matching apartments."""
        if not posts:
            return []

        self.logger.info(f"🤖 Analyzing {len(posts)} posts with AI...")

        try:
            matching_posts = self.analyzer.filter_posts(posts)
            self.logger.info(f"✅ Found {len(matching_posts)} matching apartments")
            return matching_posts
        except Exception as e:
            self.logger.error(f"❌ AI analysis failed: {e}")
            return []

    async def send_notifications(self, matching_posts: List[Dict[str, Any]]) -> int:
        """Send Telegram notifications for matching posts."""
        if not matching_posts or not self.notifier:
            return 0

        self.logger.info(f"📱 Sending {len(matching_posts)} notifications...")

        sent_count = 0
        for post in matching_posts:
            try:
                if await self.notifier.send_post_notification(post):
                    self.db.mark_post_notified(post["id"])
                    sent_count += 1
                    await asyncio.sleep(1)  # Rate limiting
            except Exception as e:
                self.logger.error(f"Failed to send notification for post {post.get('id')}: {e}")

        self.logger.info(f"📨 Sent {sent_count} notifications successfully")
        return sent_count

    async def run_single_cycle(self) -> Dict[str, int]:
        """Run one complete scraping and analysis cycle following INSTRUCTIONS.md flow."""
        start_time = datetime.now()
        self.logger.info(f"🚀 Starting scrape cycle at {start_time.strftime('%H:%M:%S')}")

        try:
            # Step 1: Scrape new posts from all groups
            new_posts = await self.scrape_all_groups()
            
            # Step 2: AI Analysis with Ollama  
            matching_posts = self.analyze_posts(new_posts)
            
            # Step 3: Send matching posts to Telegram
            notifications_sent = await self.send_notifications(matching_posts)
            
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            
            # Log summary
            self.logger.info(f"✅ Cycle complete in {duration:.1f}s - "
                           f"Scraped: {len(new_posts)}, Matches: {len(matching_posts)}, "
                           f"Sent: {notifications_sent}")

            return {
                "scraped": len(new_posts),
                "matches": len(matching_posts), 
                "sent": notifications_sent
            }

        except Exception as e:
            self.logger.error(f"❌ Cycle failed: {e}")
            return {"scraped": 0, "matches": 0, "sent": 0}

    async def run_once(self):
        """Run the bot once and exit."""
        self.logger.info("🔄 Running bot once...")

        if not await self.test_configuration():
            self.logger.error("❌ Configuration test failed")
            return False

        results = await self.run_single_cycle()
        self.logger.info(f"🏁 Single run completed: {results}")
        return True

    async def run_continuously(self):
        """Run the bot continuously with scheduled intervals."""
        self.logger.info(f"♾️  Starting continuous mode - checking every {self.scrape_interval_minutes} minutes")
        self.logger.info(f"📅 Downtime status: {self.get_downtime_status_message()}")

        if not await self.test_configuration():
            self.logger.error("❌ Configuration test failed")
            return

        cycle_count = 0

        try:
            while True:
                cycle_count += 1
                current_time = datetime.now()
                
                # Check if we're in downtime
                if self.is_downtime():
                    end_hour = (self.downtime_start_hour + self.downtime_duration_hours) % 24
                    self.logger.info(f"🌙 Cycle #{cycle_count} - Skipping scrape (downtime active until {end_hour:02d}:00)")
                else:
                    self.logger.info(f"📅 Cycle #{cycle_count} at {current_time.strftime('%H:%M:%S')}")
                    
                    # Run scraping cycle
                    await self.run_single_cycle()
                
                # Wait for next cycle
                self.logger.info(f"😴 Sleeping for {self.scrape_interval_minutes} minutes...")
                await asyncio.sleep(self.scrape_interval_minutes * 60)
                
        except KeyboardInterrupt:
            self.logger.info("⚠️  Bot stopped by user")
        except Exception as e:
            self.logger.error(f"💥 Bot crashed: {e}")
    
    async def run_test(self):
        """Test configuration and send test message."""
        self.logger.info("🧪 Running configuration test...")
        
        if await self.test_configuration():
            self.logger.info("✅ All tests passed!")
            
            # Test Facebook login
            try:
                async with FacebookScraper() as scraper:
                    await scraper.initialize_browser()
                    if await self.verify_facebook_login(scraper):
                        self.logger.info("✅ Facebook login test passed!")
                    else:
                        self.logger.error("❌ Facebook login test failed")
                        return False
            except Exception as e:
                self.logger.error(f"❌ Facebook test failed: {e}")
                return False
            
            # Send test message if Telegram is configured
            if self.notifier:
                try:
                    await self.notifier.send_test_message()
                    self.logger.info("📱 Test message sent to Telegram")
                except Exception as e:
                    self.logger.warning(f"⚠️  Test message failed: {e}")
            
            return True
        else:
            self.logger.error("❌ Configuration test failed")
            return False


async def main():
    """Main entry point."""
    bot = FacebookRentalBot()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "once":
            await bot.run_once()
        elif command == "test":
            success = await bot.run_test()
            sys.exit(0 if success else 1)
        elif command == "continuous":
            await bot.run_continuously()
        else:
            print("Usage: python main.py [once|test|continuous]")
            print("  once       - Run once and exit")
            print("  test       - Test configuration") 
            print("  continuous - Run continuously (default)")
            sys.exit(1)
    else:
        # Default: run continuously
        await bot.run_continuously()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        sys.exit(1)
