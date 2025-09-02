"""Facebook Rentals Telegram Bot - Main Package.

A Python application that scrapes posts from Facebook rental groups,
filters them using a local LLaMA model, and sends relevant results
as Telegram messages.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .analyzer import ApartmentAnalyzer
from .db import DatabaseManager
# Main components
from .main import FacebookRentalScraper
from .notifier import TelegramNotifier
from .scraper import FacebookScraper, scrape_facebook_groups

__all__ = [
  "FacebookRentalScraper",
  "FacebookScraper",
  "scrape_facebook_groups",
  "ApartmentAnalyzer",
  "TelegramNotifier",
  "DatabaseManager",
]
