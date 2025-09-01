#!/usr/bin/env python3
"""Quick test to scrape and analyze posts from a Facebook group."""

import sys
import os
import asyncio

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import FacebookScraper
from analyzer import ApartmentAnalyzer


async def quick_test(group_url: str, max_posts: int = 5):
    """Quick test to scrape and analyze Facebook group posts."""
    
    print(f"🏠 Scraping {max_posts} posts from Facebook group")
    print("=" * 50)
    
    scraper = FacebookScraper()
    analyzer = ApartmentAnalyzer()
    
    try:
        await scraper.initialize_browser()
        posts = await scraper.scrape_group_posts(group_url, max_posts=max_posts)
        
        print(f"Found {len(posts)} posts\n")
        
        matches = 0
        for i, post in enumerate(posts, 1):
            result = analyzer.analyze_post(post)
            status = "✅ MATCH" if result == "match" else "❌ NO MATCH"
            matches += 1 if result == "match" else 0
            
            print(f"Post {i}: {status}")
            print(f"  Author: {post.get('author', 'Unknown')}")
            print(f"  Content: {post.get('content', '')[:100]}...")
            print()
            
        print(f"Summary: {matches}/{len(posts)} posts matched criteria")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await scraper.cleanup()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python quick_group_test.py <facebook_group_url> [max_posts]")
        print("Example: python quick_group_test.py 'https://www.facebook.com/groups/123456' 10")
        sys.exit(1)
    
    group_url = sys.argv[1]
    max_posts = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    asyncio.run(quick_test(group_url, max_posts))
