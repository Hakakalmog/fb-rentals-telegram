#!/usr/bin/env python3
"""Debug scraper to investigate why we're only finding 1 post."""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from scraper import FacebookScraper


async def debug_facebook_selectors(group_url: str):
    """Debug Facebook selectors to see what elements are available."""
    
    print(f"🔍 Debugging Facebook group selectors")
    print("=" * 60)
    print(f"Group: {group_url}")
    
    scraper = FacebookScraper(headless=False)  # Visible browser
    
    try:
        await scraper.initialize_browser()
        print("🔄 Navigating to group...")
        await scraper.page.goto(group_url, timeout=30000)
        
        # Wait for initial load
        print("⏳ Waiting 8 seconds for page load...")
        await asyncio.sleep(8)
        
        # Check various selectors
        print("\n📋 CHECKING DIFFERENT SELECTORS:")
        print("-" * 40)
        
        # Current selector
        articles = await scraper.page.query_selector_all('[role="article"]')
        print(f"1. [role='article']: {len(articles)} elements")
        
        # Alternative selectors
        divs_with_data = await scraper.page.query_selector_all('[data-pagelet*="FeedUnit"]')
        print(f"2. [data-pagelet*='FeedUnit']: {len(divs_with_data)} elements")
        
        story_elements = await scraper.page.query_selector_all('[data-testid="story-subtitle"]')
        print(f"3. [data-testid='story-subtitle']: {len(story_elements)} elements")
        
        post_containers = await scraper.page.query_selector_all('[data-testid="fbfeed_story"]')
        print(f"4. [data-testid='fbfeed_story']: {len(post_containers)} elements")
        
        # Try more generic selectors
        divs_with_id = await scraper.page.query_selector_all('div[id*="mount_"]')
        print(f"5. div[id*='mount_']: {len(divs_with_id)} elements")
        
        # Check for feed root
        feed_root = await scraper.page.query_selector_all('[data-testid="newsfeed"]')
        print(f"6. [data-testid='newsfeed']: {len(feed_root)} elements")
        
        print(f"\n🔄 SCROLLING AND RE-CHECKING:")
        print("-" * 40)
        
        # Scroll several times and check
        for scroll_num in range(5):
            await scraper.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(4)
            
            # Check articles again
            new_articles = await scraper.page.query_selector_all('[role="article"]')
            feed_units = await scraper.page.query_selector_all('[data-pagelet*="FeedUnit"]')
            
            print(f"After scroll {scroll_num + 1}:")
            print(f"  - [role='article']: {len(new_articles)} elements")
            print(f"  - FeedUnit elements: {len(feed_units)} elements")
        
        print(f"\n📝 ANALYZING ARTICLE CONTENT:")
        print("-" * 40)
        
        final_articles = await scraper.page.query_selector_all('[role="article"]')
        print(f"Total articles found: {len(final_articles)}")
        
        for i, article in enumerate(final_articles[:10]):  # Check first 10
            try:
                text = await article.inner_text()
                text_length = len(text.strip())
                print(f"Article {i+1}: {text_length} chars")
                
                if text_length > 50:
                    print(f"  Preview: {text[:100].replace(chr(10), ' ')}...")
                elif text_length > 0:
                    print(f"  Short content: {text[:50].replace(chr(10), ' ')}")
                else:
                    print(f"  Empty content")
                    
            except Exception as e:
                print(f"Article {i+1}: Error reading - {e}")
        
        # Try alternative extraction method
        print(f"\n🧪 TRYING ALTERNATIVE EXTRACTION:")
        print("-" * 40)
        
        # Try to find posts using different approach
        all_divs = await scraper.page.query_selector_all('div')
        post_like_divs = []
        
        print(f"Total div elements on page: {len(all_divs)}")
        print("Looking for divs with post-like content...")
        
        for i, div in enumerate(all_divs[:100]):  # Check first 100 divs
            try:
                text = await div.inner_text()
                # Look for Hebrew text that might be posts
                if (len(text) > 100 and 
                    ('להשכרה' in text or 'למכירה' in text or 'דירה' in text or 'חדרים' in text)):
                    post_like_divs.append((i, text[:150]))
            except:
                continue
        
        print(f"Found {len(post_like_divs)} divs with apartment-like content:")
        for i, (div_idx, preview) in enumerate(post_like_divs[:5]):
            print(f"  {i+1}. Div {div_idx}: {preview.replace(chr(10), ' ')}...")
        
        print(f"\n⏸️ Browser staying open for manual inspection...")
        print("Check the browser window to see the actual posts")
        await asyncio.sleep(30)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        group_url = sys.argv[1]
    else:
        group_url = "https://www.facebook.com/groups/716258928467864/?sorting_setting=CHRONOLOGICAL"
    
    print("🧪 This will open a browser window to debug Facebook selectors")
    print("💡 You'll be able to see what elements are actually on the page")
    
    asyncio.run(debug_facebook_selectors(group_url))
