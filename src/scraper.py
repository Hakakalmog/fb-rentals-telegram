import asyncio
import hashlib
import logging
import os
import re
from datetime import datetime
from typing import Any

from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)


class FacebookScraper:
  """Handles Facebook group scraping using Playwright with persistent sessions."""

  def __init__(self, browser_data_dir: str = "./browser_data", headless: bool = True):
    """Initialize scraper with browser configuration."""
    self.browser_data_dir = browser_data_dir
    self.headless = headless
    self.browser = None
    self.context = None
    self.page = None

  async def __aenter__(self):
    """Async context manager entry."""
    return self

  async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit."""
    await self.cleanup()

  async def initialize_browser(self):
    """Initialize the browser with persistent context."""
    self.playwright = await async_playwright().start()

    # Create browser data directory if it doesn't exist
    os.makedirs(self.browser_data_dir, exist_ok=True)

    # Launch browser with persistent context
    self.context = await self.playwright.chromium.launch_persistent_context(
      user_data_dir=self.browser_data_dir,
      headless=self.headless,
      args=[
        "--no-sandbox",
        "--disable-blink-features=AutomationControlled",
        "--disable-web-security",
        "--disable-features=VizDisplayCompositor",
      ],
    )

    # Use the existing page from persistent context instead of creating a new one
    pages = self.context.pages
    if pages:
      # Close all extra pages except the first one to avoid multiple browser windows
      for i, page in enumerate(pages):
        if i == 0:
          self.page = page  # Use the first page
        else:
          await page.close()  # Close extra pages
    else:
      self.page = await self.context.new_page()  # Fallback: create new page if none exist

    # Set user agent to avoid detection
    await self.page.set_extra_http_headers({
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })

    logger.info("Browser initialized successfully")

  async def check_login_status(self) -> bool:
    """Check if the user is logged into Facebook."""
    try:
      await self.page.goto("https://www.facebook.com", timeout=30000)
      await self.page.wait_for_load_state("networkidle", timeout=10000)

      # Check for login indicators
      login_form = await self.page.query_selector(
        'form[data-testid="royal_login_form"]'
      )
      if login_form:
        return False

      # Check for user menu or profile link
      user_menu = await self.page.query_selector(
        '[data-testid="blue_bar_profile_link"]'
      )
      profile_link = await self.page.query_selector('a[aria-label*="Profile"]')

      return user_menu is not None or profile_link is not None
    except Exception as e:
      logger.error(f"Error checking login status: {e}")
      return False

  def generate_post_id(self, url: str, content: str, author: str) -> str:
    """Generate a unique ID for a post."""
    content_hash = hashlib.md5(
      f"{url}_{author}_{content[:100]}".encode(), usedforsecurity=False
    ).hexdigest()
    return content_hash

  async def extract_post_data(self, post_element) -> dict[str, Any] | None:
    """Extract data from a Facebook post element."""
    try:
      # Extract post URL
      post_url = ""
      try:
        # Try to find the permalink
        permalink = await post_element.query_selector(
          'a[href*="/permalink/"], a[href*="/posts/"]'
        )
        if permalink:
          post_url = await permalink.get_attribute("href")
          if post_url and not post_url.startswith("http"):
            post_url = f"https://www.facebook.com{post_url}"
      except (AttributeError, TypeError):
        pass

      # Extract post text content - simplified and more reliable approach
      content = ""

      try:
        # Get all text from the element
        full_text = await post_element.inner_text()

        # Try to find the main content within specific selectors first
        content_found = False
        content_selectors = [
          '[data-testid="post_message"]',
          '.userContent',
          'div[dir="auto"]',  # Common Facebook text container
        ]

        for selector in content_selectors:
          element = await post_element.query_selector(selector)
          if element:
            potential_content = await element.inner_text()
            # Use this content if it's substantial and not just UI elements
            if len(potential_content.strip()) > 10:
              content = potential_content.strip()
              content_found = True
              break

        # If no specific content found, clean up the full text
        if not content_found and full_text:
          lines = full_text.split('\n')
          clean_lines = []

          for line in lines:
            line = line.strip()
            # Skip empty lines and UI elements
            if not line:
              continue
            if line in ['לייק', 'השב', 'שיתוף', 'Like', 'Comment', 'Share']:
              continue
            # Skip very short time indicators
            if (('דקות' in line or 'minutes' in line or 'ש' == line or 'h' == line) and len(line) < 15):
              continue
            clean_lines.append(line)

          # Join the meaningful lines
          if clean_lines:
            content = '\n'.join(clean_lines)

      except Exception as e:
        logger.debug(f"Error extracting post content: {e}")

      # Extract author name
      author = ""
      try:
        author_selectors = [
          "strong a",
          "h3 a",
          '[data-testid="story-subtitle"] a',
          ".actor a",
        ]

        for selector in author_selectors:
          author_element = await post_element.query_selector(selector)
          if author_element:
            author = await author_element.inner_text()
            break
      except (AttributeError, TypeError):
        pass

      # Extract timestamp
      timestamp = datetime.now()
      try:
        time_selectors = [
          'a[role="link"] abbr',
          "abbr[data-utime]",
          "time",
          ".timestamp",
        ]

        for selector in time_selectors:
          time_element = await post_element.query_selector(selector)
          if time_element:
            time_text = (
              await time_element.get_attribute("title")
              or await time_element.inner_text()
            )
            if time_text:
              # Parse time_text to datetime if possible
              # For now, use current timestamp
              break
      except (AttributeError, TypeError, ValueError):
        pass

      # Extract price from content using regex (not used in output)
      # price = self.extract_price_from_text(content)

      # Extract location from content (not used in output)  
      # location = self.extract_location_from_text(content)

      # Skip posts with no meaningful content (be less strict)
      if not content.strip():
        logger.debug("Skipping post with no content")
        return None

      # More lenient filtering - only skip very short content
      if len(content.strip()) < 5:
        logger.debug(f"Skipping very short content: {content[:50]}")
        return None

      # Generate unique post ID
      post_id = self.generate_post_id(post_url, content[:50], author)

      return {
        "id": post_id,
        "url": post_url,
        "content": content,
        "author": author,
        "timestamp": timestamp.isoformat(),
      }

    except Exception as e:
      logger.error(f"Error extracting post data: {e}")
      return None

  def extract_price_from_text(self, text: str) -> str | None:
    """Extract price information from post text."""
    # Common price patterns
    price_patterns = [
      r"\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
      r"(\d{1,3}(?:,\d{3})*)\s*(?:dollars?|\$)",
      r"(\d+)\s*k(?:\s*(?:per|/)\s*month)?",
      r"(\d+)k/mo",
    ]

    for pattern in price_patterns:
      match = re.search(pattern, text, re.IGNORECASE)
      if match:
        return match.group(0)

    return None

  def extract_location_from_text(self, text: str) -> str | None:
    """Extract location information from post text."""
    # Common location patterns
    location_patterns = [
      r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})\b",  # City, State
      r"\b(Manhattan|Brooklyn|Queens|Bronx|Staten Island)\b",
      r"\b([A-Z][a-z]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd))\b",
    ]

    for pattern in location_patterns:
      match = re.search(pattern, text, re.IGNORECASE)
      if match:
        return match.group(0)

    return None

  async def scroll_and_load_posts(self, max_posts: int = 50):
    """Scroll the page to load more posts."""
    posts_loaded = 0
    scroll_attempts = 0
    max_scroll_attempts = 10

    while posts_loaded < max_posts and scroll_attempts < max_scroll_attempts:
      # Scroll down
      await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
      await asyncio.sleep(2)

      # Wait for new content to load
      try:
        await self.page.wait_for_load_state("networkidle", timeout=5000)
      except TimeoutError:
        pass

      scroll_attempts += 1

      # Count current posts
      posts = await self.page.query_selector_all(
        '[role="article"], div[data-pagelet*="FeedUnit"]'
      )
      posts_loaded = len(posts)

      logger.debug(f"Loaded {posts_loaded} posts after {scroll_attempts} scrolls")

      if scroll_attempts >= 3 and posts_loaded == 0:
        break

  async def extract_group_name(self) -> str:
    """Extract the Facebook group name from the current page."""
    try:
      # Try multiple selectors for group name
      group_name_selectors = [
        "h1[data-testid='group-name']",
        "h1[dir='auto']", 
        "h1 span",
        "[data-testid='group-name'] span",
        "h1",
        ".x1heor9g .x1qlqyl8 .x1pd3egz .x1a2a7pz span"
      ]
      
      for selector in group_name_selectors:
        try:
          element = await self.page.query_selector(selector)
          if element:
            name = await element.inner_text()
            name = name.strip()
            if name and len(name) > 0 and "Facebook" not in name:
              logger.debug(f"Found group name with selector '{selector}': {name}")
              return name
        except Exception as e:
          logger.debug(f"Failed to get group name with selector '{selector}': {e}")
          continue
      
      # Fallback: try to extract from page title
      try:
        title = await self.page.title()
        if title and " | " in title:
          group_name = title.split(" | ")[0].strip()
          if group_name and "Facebook" not in group_name:
            logger.debug(f"Extracted group name from title: {group_name}")
            return group_name
      except Exception as e:
        logger.debug(f"Failed to extract group name from title: {e}")
      
      logger.warning("Could not extract group name, using fallback")
      return "Unknown Group"
      
    except Exception as e:
      logger.error(f"Error extracting group name: {e}")
      return "Unknown Group"

  async def scrape_group_posts(
    self, group_url: str, max_posts: int = 50
  ) -> list[dict[str, Any]]:
    """Scrape posts from a Facebook group."""
    try:
      logger.info(f"Scraping posts from: {group_url}")

      await self.page.goto(group_url, timeout=30000)

      # Simple wait for initial load
      logger.info("Waiting 5 seconds for initial page load...")
      await asyncio.sleep(5)

      # Scroll to load more posts
      logger.info("Scrolling to load more posts...")
      for scroll in range(3):
        logger.debug(f"Scroll {scroll + 1}/3...")
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(3)      # Find all post elements - use simple approach with filtering
      all_elements = await self.page.query_selector_all('[role="article"]')
      logger.info(f"Found {len(all_elements)} total elements")

      # Filter out empty elements first
      post_elements = []
      for i, element in enumerate(all_elements):
        try:
          text = await element.inner_text()
          if len(text.strip()) > 20:  # Only keep elements with substantial content
            post_elements.append(element)
            logger.debug(f"Element {i+1}: {len(text)} chars - kept")
        except Exception as e:
          logger.debug(f"Element {i+1}: Error getting text - {e}")

      logger.info(f"Filtered to {len(post_elements)} substantial post elements")

      # Extract group name once for all posts
      group_name = await self.extract_group_name()
      logger.info(f"Group name: {group_name}")

      extracted_posts = []
      processed_urls = set()  # Track URLs to avoid duplicates

      for i, post_element in enumerate(post_elements):
        try:
          logger.debug(f"Processing post element {i+1}/{len(post_elements)}...")
          post_data = await self.extract_post_data(post_element)
          if post_data:
            # Check for duplicate URLs
            post_url = post_data.get('url', '')
            if post_url in processed_urls:
              logger.debug(f"Skipping duplicate URL: {post_url[:50]}...")
              continue
            processed_urls.add(post_url)

            # Skip comments (they have comment_id in URL)
            if 'comment_id=' in post_url:
              logger.debug(f"Skipping comment: {post_data['content'][:50]}...")
              continue

            # Only keep posts with substantial content (already filtered above, but double-check)
            if len(post_data['content'].strip()) > 15:
              post_data["group_url"] = group_url
              post_data["group_name"] = group_name
              extracted_posts.append(post_data)
              logger.info(f"✅ Extracted post {len(extracted_posts)}: {post_data.get('author', 'No author')} - {post_data['content'][:50]}...")

              # Stop when we have enough posts
              if len(extracted_posts) >= max_posts:
                break
            else:
              logger.debug(f"Skipping post with short content: {len(post_data['content'])} chars")
          else:
            logger.debug(f"Post element {i+1} returned no data")

        except Exception as e:
          logger.error(f"Error processing post {i+1}: {e}")
          continue

      logger.info(
        f"Successfully extracted {len(extracted_posts)} posts from {group_url}"
      )
      return extracted_posts

    except Exception as e:
      logger.error(f"Error scraping group {group_url}: {e}")
      return []

  async def handle_group_access(self):
    """Handle group access requirements (join group, dismiss popups, etc.)."""
    try:
      # Wait for page to load
      await asyncio.sleep(3)

      # Handle "Join Group" if present
      join_button = await self.page.query_selector(
        'div[aria-label="Join Group"], button:has-text("Join")'
      )
      if join_button:
        logger.info("Found join group button, clicking...")
        await join_button.click()
        await asyncio.sleep(2)

      # Handle any modal dialogs or popups
      modal_selectors = [
        '[role="dialog"] button:has-text("Cancel")',
        '[role="dialog"] button:has-text("Not Now")',
        '[aria-label="Close"]',
        'div[data-testid="modal-close-button"]',
      ]

      for selector in modal_selectors:
        try:
          modal_button = await self.page.query_selector(selector)
          if modal_button:
            await modal_button.click()
            await asyncio.sleep(1)
        except (AttributeError, TypeError):
          pass

    except Exception as e:
      logger.debug(f"Error handling group access: {e}")

  async def cleanup(self):
    """Clean up browser resources."""
    try:
      if self.page:
        await self.page.close()
      if self.context:
        await self.context.close()
      if hasattr(self, "playwright"):
        await self.playwright.stop()
      logger.info("Browser cleanup completed")
    except Exception as e:
      logger.error(f"Error during browser cleanup: {e}")


# Async context manager usage example
async def scrape_facebook_groups(
  group_urls: list[str], max_posts_per_group: int = 50, headless: bool = True
) -> list[dict[str, Any]]:
  """Scrape posts from multiple Facebook groups."""
  all_posts = []

  async with FacebookScraper(headless=headless) as scraper:
    await scraper.initialize_browser()

    # Check if logged in
    is_logged_in = await scraper.check_login_status()
    if not is_logged_in:
      logger.error("Not logged into Facebook. Please log in manually first.")
      return []

    for group_url in group_urls:
      posts = await scraper.scrape_group_posts(group_url, max_posts_per_group)
      all_posts.extend(posts)

      # Add delay between groups to avoid rate limiting
      await asyncio.sleep(5)

  return all_posts
