"""Pytest configuration and fixtures for Facebook Rentals Telegram Bot tests."""

import asyncio
import sys
from pathlib import Path

import pytest

# Add src directory to Python path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@pytest.fixture(scope="session")
def event_loop():
  """Create an instance of the default event loop for the test session."""
  loop = asyncio.get_event_loop_policy().new_event_loop()
  yield loop
  loop.close()


@pytest.fixture
def sample_post():
  """Sample Facebook post data for testing."""
  return {
    "id": "test_post_123",
    "post_id": "test_post_123",
    "author": "Test User",
    "content": "Looking for a 2BR apartment in Tel Aviv, max 2000 NIS",
    "timestamp": "2025-08-17 10:30:00",
    "link": "https://facebook.com/groups/test/posts/123",
    "group_url": "https://facebook.com/groups/test",
    "scraped_at": "2025-08-17 10:31:00",
  }


@pytest.fixture
def sample_posts_list(sample_post):
  """List of sample posts for testing."""
  posts = []
  for i in range(5):
    post = sample_post.copy()
    post["id"] = f"test_post_{i}"
    post["post_id"] = f"test_post_{i}"
    post["content"] = f"Test post content {i}"
    posts.append(post)
  return posts


@pytest.fixture
def mock_env_vars(monkeypatch):
  """Mock environment variables for testing."""
  env_vars = {
    "TELEGRAM_BOT_TOKEN": "test_bot_token",
    "TELEGRAM_CHAT_ID": "test_chat_id",
    "FB_GROUP_URLS": "https://facebook.com/groups/test1,https://facebook.com/groups/test2",
    "MAX_PRICE": "2000",
    "LOCATION_KEYWORDS": "tel aviv,ramat gan",
    "OLLAMA_HOST": "http://localhost:11434",
    "OLLAMA_MODEL": "llama3.2:3b",
    "DATABASE_PATH": ":memory:",
    "LOG_LEVEL": "DEBUG",
  }

  for key, value in env_vars.items():
    monkeypatch.setenv(key, value)

  return env_vars
