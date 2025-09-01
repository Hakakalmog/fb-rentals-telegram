#!/usr/bin/env python3
"""Debug scraper to see what Facebook is actually showing."""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scraper import FacebookScraper


async def debug_facebook_group(group_url: str):
    """Debug what Facebook is actually showing in a group."""
    
    print(f"🔍 Debugging Facebook group: {group_url}")
    print("=" * 60)
    
    scraper = FacebookScraper(headless=False)  # Show browser so you can see
    
    try:
        await scraper.initialize_browser()
        await scraper.page.goto(group_url, timeout=30000)
        
        print("🔄 Waiting 5 seconds for page load...")
        await asyncio.sleep(5)
        
        # Check what elements exist
        all_articles = await scraper.page.query_selector_all('[role="article"]')
        print(f"📄 Found {len(all_articles)} [role='article'] elements")
        
        # Check for other possible post selectors
        divs_with_data = await scraper.page.query_selector_all('[data-pagelet]')
        print(f"📄 Found {len(divs_with_data)} [data-pagelet] elements")
        
        # Check for feed elements
        feed_elements = await scraper.page.query_selector_all('[data-pagelet*="FeedUnit"]')
        print(f"📄 Found {len(feed_elements)} feed unit elements")
        
        # Try scrolling and see if more appear
        print("\n🔄 Scrolling to load more content...")
        for i in range(5):
            await scraper.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(3)
            
            new_articles = await scraper.page.query_selector_all('[role="article"]')
            print(f"   After scroll {i+1}: {len(new_articles)} articles")
        
        # Try to extract content from what we found
        print(f"\n📝 Analyzing the {len(all_articles)} article elements:")
        for i, article in enumerate(all_articles[:10]):  # Check first 10
            try:
                text = await article.inner_text()
                if len(text.strip()) > 20:
                    print(f"   Article {i+1}: {len(text)} chars - '{text[:100]}...'")
                else:
                    print(f"   Article {i+1}: {len(text)} chars - too short")
            except Exception as e:
                print(f"   Article {i+1}: Error - {e}")
        
        print("\n⏸️  Browser will stay open for 30 seconds so you can inspect manually...")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Use the working group as default
        group_url = "https://www.facebook.com/groups/716258928467864/?sorting_setting=CHRONOLOGICAL"
    else:
        group_url = sys.argv[1]
    
    print("🧪 This will open Facebook in a visible browser window")
    print("💡 You can see exactly what posts Facebook is showing")
    
    asyncio.run(debug_facebook_group(group_url))
