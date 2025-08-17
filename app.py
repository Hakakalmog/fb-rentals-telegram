#!/usr/bin/env python3
"""Facebook Rentals Telegram Bot - Main Entry Point.

Usage:
  python app.py [once|test|continuous]

Commands:
  once: Run scraper once and exit
  test: Test configuration and send test message
  continuous: Run scraper continuously (default)
"""

import asyncio
import os
import sys

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from main import main  # noqa: E402

if __name__ == "__main__":
  try:
    asyncio.run(main())
  except KeyboardInterrupt:
    print("\nShutdown requested by user")
  except Exception as e:
    print(f"Fatal error: {e}")
    import logging

    logging.error(f"Fatal error: {e}")
    sys.exit(1)
