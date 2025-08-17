import logging
import os
import sqlite3
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseManager:
  """Manages SQLite database operations for storing and tracking rental posts."""

  def __init__(self, db_path: str):
    """Initialize database manager with specified path."""
    self.db_path = db_path
    self.ensure_db_directory()
    self.init_database()

  def ensure_db_directory(self):
    """Ensure the database directory exists."""
    db_dir = os.path.dirname(self.db_path)
    if db_dir and not os.path.exists(db_dir):
      os.makedirs(db_dir, exist_ok=True)

  def init_database(self):
    """Initialize the database with required tables."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()

      # Create posts table
      cursor.execute(
        """
  CREATE TABLE IF NOT EXISTS posts (
          id TEXT PRIMARY KEY,
          url TEXT NOT NULL,
          title TEXT NOT NULL,
          content TEXT NOT NULL,
          price TEXT,
          location TEXT,
          author TEXT,
          timestamp DATETIME NOT NULL,
          group_url TEXT NOT NULL,
          scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP,
          notified BOOLEAN DEFAULT FALSE,
          relevance_score REAL DEFAULT 0.0
  )
      """
      )

      # Create index for faster lookups
      cursor.execute(
        """
  CREATE INDEX IF NOT EXISTS idx_posts_url ON posts(url)
      """
      )
      cursor.execute(
        """
  CREATE INDEX IF NOT EXISTS idx_posts_timestamp ON posts(timestamp)
      """
      )
      cursor.execute(
        """
  CREATE INDEX IF NOT EXISTS idx_posts_notified ON posts(notified)
      """
      )

      conn.commit()
      logger.info("Database initialized successfully")

  def post_exists(self, post_id: str) -> bool:
    """Check if a post already exists in the database."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,))
      return cursor.fetchone() is not None

  def save_post(self, post_data: dict[str, Any]) -> bool:
    """Save a post to the database."""
    try:
      with sqlite3.connect(self.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
          """
          INSERT OR REPLACE INTO posts
          (id, url, title, content, price, location, author, timestamp, group_url, relevance_score)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
  """,
          (
            post_data["id"],
            post_data["url"],
            post_data["title"],
            post_data["content"],
            post_data.get("price"),
            post_data.get("location"),
            post_data.get("author"),
            post_data["timestamp"],
            post_data["group_url"],
            post_data.get("relevance_score", 0.0),
          ),
        )
        conn.commit()
        return True
    except Exception as e:
      logger.error(f"Error saving post to database: {e}")
      return False

  def get_unnotified_posts(self) -> list[dict[str, Any]]:
    """Get all posts that haven't been notified yet."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute(
        """
  SELECT id, url, title, content, price, location, author, timestamp, group_url, relevance_score
  FROM posts
  WHERE notified = FALSE
  ORDER BY timestamp DESC
      """
      )

      posts = []
      for row in cursor.fetchall():
        posts.append(
          {
            "id": row[0],
            "url": row[1],
            "title": row[2],
            "content": row[3],
            "price": row[4],
            "location": row[5],
            "author": row[6],
            "timestamp": row[7],
            "group_url": row[8],
            "relevance_score": row[9],
          }
        )
      return posts

  def mark_post_notified(self, post_id: str):
    """Mark a post as notified."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute("UPDATE posts SET notified = TRUE WHERE id = ?", (post_id,))
      conn.commit()

  def get_post_count(self) -> int:
    """Get total number of posts in database."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute("SELECT COUNT(*) FROM posts")
      return cursor.fetchone()[0]

  def cleanup_old_posts(self, days: int = 30):
    """Remove posts older than specified days."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute(
        """
  DELETE FROM posts
  WHERE scraped_at < datetime('now', '-' || ? || ' days')
      """,
        (days,),
      )
      deleted_count = cursor.rowcount
      conn.commit()
      logger.info(f"Cleaned up {deleted_count} old posts")

  def get_recent_posts(self, hours: int = 24) -> list[dict[str, Any]]:
    """Get posts from the last N hours."""
    with sqlite3.connect(self.db_path) as conn:
      cursor = conn.cursor()
      cursor.execute(
        """
  SELECT id, url, title, content, price, location, author, timestamp, group_url, relevance_score
  FROM posts
  WHERE scraped_at > datetime('now', '-' || ? || ' hours')
  ORDER BY timestamp DESC
      """,
        (hours,),
      )

      posts = []
      for row in cursor.fetchall():
        posts.append(
          {
            "id": row[0],
            "url": row[1],
            "title": row[2],
            "content": row[3],
            "price": row[4],
            "location": row[5],
            "author": row[6],
            "timestamp": row[7],
            "group_url": row[8],
            "relevance_score": row[9],
          }
        )
      return posts
