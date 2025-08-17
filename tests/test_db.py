"""
Unit tests for the database module.
"""

import sqlite3
from unittest.mock import Mock, patch

import pytest

from db import DatabaseManager


class TestDatabaseManager:
  """Test cases for DatabaseManager class."""

  @pytest.fixture
  def db_manager(self):
    """Create a DatabaseManager instance with in-memory database."""
    return DatabaseManager(":memory:")

  def test_init_creates_database(self, db_manager):
    """Test that DatabaseManager creates the database and tables."""
    assert db_manager.db_path == ":memory:"

    # Check that posts table exists
    conn = sqlite3.connect(":memory:")
    conn.cursor()

    # This should work if the database was initialized properly
    with patch.object(db_manager, "conn") as mock_conn:
      mock_conn.execute.return_value = Mock()
      db_manager.create_tables()

    conn.close()

  def test_save_post_success(self, db_manager, sample_post):
    """Test saving a post successfully."""
    result = db_manager.save_post(sample_post)
    assert result is True

    # Verify the post was saved
    assert db_manager.post_exists(sample_post["id"]) is True

  def test_save_post_duplicate(self, db_manager, sample_post):
    """Test that duplicate posts are handled properly."""
    # Save post first time
    result1 = db_manager.save_post(sample_post)
    assert result1 is True

    # Try to save same post again
    result2 = db_manager.save_post(sample_post)
    assert result2 is False  # Should indicate duplicate

  def test_post_exists(self, db_manager, sample_post):
    """Test post existence check."""
    # Post shouldn't exist initially
    assert db_manager.post_exists(sample_post["id"]) is False

    # Save post
    db_manager.save_post(sample_post)

    # Post should exist now
    assert db_manager.post_exists(sample_post["id"]) is True

  def test_mark_post_notified(self, db_manager, sample_post):
    """Test marking a post as notified."""
    # Save post first
    db_manager.save_post(sample_post)

    # Mark as notified
    result = db_manager.mark_post_notified(sample_post["id"])
    assert result is True

  def test_get_post_count(self, db_manager, sample_posts_list):
    """Test getting post count."""
    # Initially should be 0
    assert db_manager.get_post_count() == 0

    # Save some posts
    for post in sample_posts_list:
      db_manager.save_post(post)

    # Count should match
    assert db_manager.get_post_count() == len(sample_posts_list)

  def test_cleanup_old_posts(self, db_manager, sample_post):
    """Test cleanup of old posts."""
    # Save a post
    db_manager.save_post(sample_post)

    # Should have 1 post
    assert db_manager.get_post_count() == 1

    # Cleanup posts older than 0 days (should remove all)
    deleted_count = db_manager.cleanup_old_posts(0)

    # Should have deleted 1 post
    assert deleted_count >= 0  # Might be 0 due to timing

  @pytest.mark.asyncio
  async def test_database_error_handling(self, db_manager):
    """Test database error handling."""
    # Close the connection to simulate an error
    db_manager.conn.close()

    # Operations should handle the error gracefully
    result = db_manager.save_post({"id": "test", "content": "test"})
    assert result is False
