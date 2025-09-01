import asyncio
import html
import logging
import re
from typing import Any

from telegram import Bot
from telegram.constants import ParseMode

logger = logging.getLogger(__name__)


class TelegramNotifier:
  """Handles Telegram notifications for rental posts with rich formatting."""

  def __init__(self, bot_token: str, chat_id: str):
    """Initialize Telegram bot with credentials."""
    self.bot_token = bot_token
    self.chat_id = chat_id
    self.bot = Bot(token=bot_token)

  async def test_connection(self) -> bool:
    """Test if the bot can connect to Telegram."""
    try:
      await self.bot.get_me()
      logger.info("Telegram bot connection successful")
      return True
    except Exception as e:
      logger.error(f"Failed to connect to Telegram: {e}")
      return False

  def format_post_message(self, post: dict[str, Any]) -> str:
    """Format a post as a Telegram message."""
    try:
      content = post.get("content", "")
      author = post.get("author", "Unknown")
      url = post.get("url", "")
      group_url = post.get("group_url", "")
      timestamp = post.get("timestamp", "")

      # Clean and truncate content for better readability
      content = self.clean_text_for_telegram(content)
      if len(content) > 1000:  # Telegram message limit consideration
        content = content[:1000] + "..."

      # Build message
      message_parts = []

      # Title/Header with emoji
      message_parts.append("🏠 *New Rental Post*")

      # Author
      if author:
        message_parts.append(f"👤 *Author:* {html.escape(author)}")

      # Timestamp
      if timestamp:
        try:
          from datetime import datetime
          dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
          formatted_time = dt.strftime("%Y-%m-%d %H:%M")
          message_parts.append(f"⏰ *Posted:* {formatted_time}")
        except:
          message_parts.append(f"⏰ *Posted:* {timestamp[:19]}")

      # Content
      if content:
        message_parts.append(f"📝 *Content:*\n{html.escape(content)}")

      # URLs
      if url:
        message_parts.append(f"🔗 [View Post]({url})")

      # Group info - use group_name if available, fallback to extracting from URL
      group_name = post.get('group_name')
      if not group_name and group_url:
        group_name = self.extract_group_name_from_url(group_url)
      
      if group_name:
        message_parts.append(f"👥 *Group:* {group_name}")

      # Separator
      message_parts.append("➖" * 20)

      return "\n\n".join(message_parts)

    except Exception as e:
      logger.error(f"Error formatting post message: {e}")
      return f"Error formatting message for post: {post.get('id', 'Unknown')}"

  def clean_text_for_telegram(self, text: str) -> str:
    """Clean text for Telegram formatting."""
    if not text:
      return ""

    # Remove excessive whitespace
    text = re.sub(r"\s+", " ", text.strip())

    # Remove Facebook-specific elements
    text = re.sub(r"See more$", "", text)
    text = re.sub(r"See translation$", "", text)
    text = re.sub(r"\n+", "\n", text)

    return text

  def extract_group_name_from_url(self, group_url: str) -> str:
    """Extract a readable group name from the URL."""
    try:
      # Extract group ID or name from URL
      if "/groups/" in group_url:
        group_part = group_url.split("/groups/")[1].split("/")[0]
        # Remove URL parameters
        group_part = group_part.split("?")[0]
        return group_part.replace("_", " ").title()
      return "Facebook Group"
    except (IndexError, AttributeError):
      return "Facebook Group"

  async def send_post_notification(self, post: dict[str, Any]) -> bool:
    """Send a notification for a single post."""
    try:
      message = self.format_post_message(post)

      await self.bot.send_message(
        chat_id=self.chat_id,
        text=message,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
      )

      logger.info(f"Sent notification for post: {post.get('id', 'Unknown')}")
      return True

    except Exception as e:
      logger.error(
        f"Failed to send notification for post {post.get('id', 'Unknown')}: {e}"
      )
      # Try sending without markdown formatting as fallback
      try:
        simple_message = self.create_simple_message(post)
        await self.bot.send_message(
          chat_id=self.chat_id,
          text=simple_message,
          disable_web_page_preview=True,
        )
        logger.info(
          f"Sent simple notification for post: {post.get('id', 'Unknown')}"
        )
        return True
      except Exception as e2:
        logger.error(f"Failed to send simple notification: {e2}")
        return False

  def create_simple_message(self, post: dict[str, Any]) -> str:
    """Create a simple text message without markdown formatting."""
    content = post.get("content", "")[:800]  # Increased limit since no other fields
    author = post.get("author", "Unknown")
    url = post.get("url", "")
    timestamp = post.get("timestamp", "")

    message = "🏠 New Rental Post\n\n"
    message += f"Author: {author}\n"
    
    if timestamp:
      message += f"Posted: {timestamp[:19]}\n"
    
    message += f"Content: {content}\n"

    if url:
      message += f"\nView: {url}"

    return message

  async def send_summary_notification(
    self, posts_count: int, relevant_count: int
  ) -> bool:
    """Send a summary notification."""
    try:
      message = "📊 *Scraping Summary*\n\n"
      message += f"🔍 Posts scraped: {posts_count}\n"
      message += f"✅ Relevant posts: {relevant_count}\n"
      message += f"⏰ Time: {self.get_current_time()}"

      await self.bot.send_message(
        chat_id=self.chat_id, text=message, parse_mode=ParseMode.MARKDOWN
      )

      logger.info("Sent summary notification")
      return True

    except Exception as e:
      logger.error(f"Failed to send summary notification: {e}")
      return False

  async def send_error_notification(self, error_message: str) -> bool:
    """Send an error notification."""
    try:
      message = "⚠️ *Scraper Error*\n\n"
      message += f"Error: {html.escape(error_message)}\n"
      message += f"Time: {self.get_current_time()}"

      await self.bot.send_message(
        chat_id=self.chat_id, text=message, parse_mode=ParseMode.MARKDOWN
      )

      logger.info("Sent error notification")
      return True

    except Exception as e:
      logger.error(f"Failed to send error notification: {e}")
      return False

  def get_current_time(self) -> str:
    """Get current time as a formatted string."""
    from datetime import datetime

    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  async def notify_posts(self, posts: list[dict[str, Any]]) -> int:
    """Send notifications for multiple posts."""
    success_count = 0

    for post in posts:
      try:
        if await self.send_post_notification(post):
          success_count += 1

        # Add small delay to avoid rate limiting
        await asyncio.sleep(1)

      except Exception as e:
        logger.error(
          f"Error in notify_posts for post {post.get('id', 'Unknown')}: {e}"
        )

    logger.info(f"Successfully sent {success_count}/{len(posts)} notifications")
    return success_count

  async def send_test_message(self) -> bool:
    """Send a test message to verify the bot is working."""
    try:
      message = "🤖 Test message from FB Rentals Bot\n\nIf you see this, the bot is working correctly!"

      await self.bot.send_message(chat_id=self.chat_id, text=message)

      logger.info("Test message sent successfully")
      return True

    except Exception as e:
      logger.error(f"Failed to send test message: {e}")
      return False
