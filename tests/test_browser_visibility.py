#!/usr/bin/env python3
"""
Test script to check if browser window is visible
"""

import asyncio
import os
import sys

from playwright.async_api import async_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


async def test_browser_visibility():
    """Test if browser window opens visibly."""
    print("🧪 Testing Browser Visibility")
    print("=" * 50)

    async with async_playwright() as p:
        print("🌐 Opening browser with maximum visibility...")

        # Try with regular launch first (not persistent context)
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--new-window",
                "--start-maximized",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ]
        )

        context = await browser.new_context()
        page = await context.new_page()

        print("🎯 Browser should be visible now!")
        print("📝 Going to Facebook...")

        await page.goto("https://www.facebook.com", timeout=30000)

        print("⏳ Waiting 10 seconds for you to see the browser...")
        await asyncio.sleep(10)

        print("✅ Closing browser")
        await browser.close()

    print("🎉 Test completed - did you see the browser window?")

if __name__ == "__main__":
    asyncio.run(test_browser_visibility())
