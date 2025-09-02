#!/usr/bin/env python3
"""Manual test to scrape 5 posts from a specific Facebook group a        'analysis_criteria': {
            'rooms': '3+ rooms required',
            'price': 'max 5,900₪ per month',
            'type': 'rental only (not sale)'
        },
        'ollama_model': os.getenv("OLLAMA_MODEL", "llama3.1:latest"),
        'posts_with_analysis': posts_with_analysisyze them."""

import sys
import os
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from scraper import FacebookScraper
from analyzer import ApartmentAnalyzer


def save_scraped_posts(posts, group_url):
    """Save scraped posts to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract group ID from URL more reliably  
    group_id = "unknown"
    if 'groups/' in group_url:
        try:
            # Extract the numeric ID from the URL
            parts = group_url.split('groups/')[1].split('/')[0].split('?')[0]
            if parts.isdigit():
                group_id = parts
        except:
            group_id = "unknown"
    
    filename = f"scraped_posts_{group_id}_{timestamp}.json"
    filepath = os.path.join(os.path.dirname(__file__), '..', 'test_outputs', 'scraped_posts', filename)
    
    # Create data structure to save
    data = {
        'timestamp': timestamp,
        'group_url': group_url,
        'group_id': group_id,
        'total_posts': len(posts),
        'posts': posts
    }
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Scraped posts saved to: {filepath}")
    return filepath


def save_ollama_results(posts_with_analysis, group_url, scraped_file_path):
    """Save Ollama analysis results to JSON file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Extract group ID from URL more reliably
    group_id = "unknown"
    if 'groups/' in group_url:
        try:
            parts = group_url.split('groups/')[1].split('/')[0].split('?')[0]
            if parts.isdigit():
                group_id = parts
        except:
            group_id = "unknown"
    
    filename = f"ollama_results_{group_id}_{timestamp}.json"
    filepath = os.path.join(os.path.dirname(__file__), '..', 'test_outputs', 'ollama_posts', filename)
    
    # Count matches
    matches = [p for p in posts_with_analysis if p.get('ollama_result') == 'match']
    no_matches = [p for p in posts_with_analysis if p.get('ollama_result') == 'no match']
    
    # Create analysis summary
    data = {
        'timestamp': timestamp,
        'group_url': group_url,
        'group_id': group_id,
        'scraped_from_file': os.path.basename(scraped_file_path),
        'analysis_summary': {
            'total_posts_analyzed': len(posts_with_analysis),
            'matches_found': len(matches),
            'no_matches_found': len(no_matches),
            'match_rate': f"{(len(matches)/len(posts_with_analysis))*100:.1f}%" if posts_with_analysis else "0%"
        },
        'criteria': {
            'rooms': '3+ rooms required',
            'price': 'max 5,900₪ per month',
            'type': 'rental only (not sale)'
        },
        'ollama_model': 'llama3.1:70b',
        'posts_with_analysis': posts_with_analysis
    }
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"🤖 Ollama analysis results saved to: {filepath}")
    return filepath


class EnhancedFacebookScraper(FacebookScraper):
    """Enhanced scraper with more aggressive scrolling for testing."""
    
    async def scrape_group_posts_enhanced(self, group_url: str, max_posts: int = 3):
        """Scrape posts with more aggressive scrolling."""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            logger.info(f"Enhanced scraping from: {group_url}")
            await self.page.goto(group_url, timeout=30000)
            
            # Wait for initial load
            print("   • Loading page...")
            await self.page.wait_for_timeout(5000)
            
            # More aggressive scrolling to find posts
            print("   • Scrolling to load more posts...")
            for scroll in range(12):  # Increased scrolling attempts
                print(f"     - Scroll {scroll + 1}/12...")
                await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await self.page.wait_for_timeout(4000)  # Wait longer between scrolls
                
                # Check how many articles we have so far
                current_articles = await self.page.query_selector_all('[role="article"]')
                print(f"     - Found {len(current_articles)} article elements so far")
                
                # Also try alternative selectors for posts
                feed_units = await self.page.query_selector_all('[data-pagelet*="FeedUnit"]')
                other_posts = await self.page.query_selector_all('[data-testid="story-subtitle"]')
                
                total_elements = len(current_articles) + len(feed_units) + len(other_posts)
                print(f"     - Total potential post elements: {total_elements}")
                
                if total_elements >= max_posts * 3:  # Stop if we have enough
                    print(f"     - Stopping scroll, found enough elements")
                    break
            
            # Use the parent class method to extract posts
            all_elements = await self.page.query_selector_all('[role="article"]')
            print(f"   • Total article elements found: {len(all_elements)}")
            
            # Filter elements with content
            post_elements = []
            for i, element in enumerate(all_elements):
                try:
                    text = await element.inner_text()
                    if len(text.strip()) > 20:
                        post_elements.append(element)
                except:
                    continue
                    
            print(f"   • Elements with substantial content: {len(post_elements)}")
            
            # Extract group name
            group_name = await self.extract_group_name()
            
            # Extract posts
            extracted_posts = []
            processed_urls = set()
            
            for i, post_element in enumerate(post_elements[:max_posts * 3]):  # Check more elements
                try:
                    post_data = await self.extract_post_data(post_element)
                    if post_data:
                        post_url = post_data.get('url', '')
                        if post_url in processed_urls or 'comment_id=' in post_url:
                            continue
                        processed_urls.add(post_url)
                        
                        if len(post_data['content'].strip()) > 15:
                            post_data["group_url"] = group_url
                            post_data["group_name"] = group_name
                            extracted_posts.append(post_data)
                            print(f"   • Extracted post {len(extracted_posts)}: {post_data['content'][:50]}...")
                            
                            if len(extracted_posts) >= max_posts:
                                break
                except Exception as e:
                    continue
                    
            return extracted_posts
            
        except Exception as e:
            logger.error(f"Enhanced scraping error: {e}")
            return []


async def test_manual_group_scraping(group_url: str):
    """
    Scrape first 3 posts from a specified Facebook group and analyze each one.
    
    Args:
        group_url: The Facebook group URL to scrape
    """
    print("🏠 Manual Facebook Group Apartment Analysis Test")
    print("=" * 60)
    print(f"📍 Target Group: {group_url}")
    print("🎯 Analyzing first 3 posts with binary classification")
    print("📋 Criteria: 3+ rooms, max 5,900₪, rental (not sale)")
    print()
    
    # Initialize components
    scraper = FacebookScraper(headless=False)  # Use visible mode like manual_login_test.py
    analyzer = ApartmentAnalyzer()
    
    try:
        print("🔄 Starting browser and navigating to group...")
        
        # Initialize the scraper
        await scraper.initialize_browser()
        
        # Check if we're logged into Facebook (with shorter timeout)
        print("🔍 Checking Facebook login status...")
        try:
            # Try to navigate to Facebook first
            await scraper.page.goto("https://www.facebook.com", timeout=15000)
            await scraper.page.wait_for_timeout(2000)
            
            # Quick login check - if we can access Facebook main page, assume we're logged in
            current_url = scraper.page.url
            if "facebook.com" in current_url and "login" not in current_url.lower():
                print("✅ Already logged into Facebook!")
                is_logged_in = True
            else:
                is_logged_in = False
        except Exception as e:
            print(f"⚠️  Could not verify login status: {e}")
            print("🔄 Proceeding anyway - if you see login issues, run manual_login_test.py first")
            is_logged_in = True  # Proceed anyway
        
        if not is_logged_in:
            print("\n" + "="*60)
            print("🔑 LOGIN REQUIRED")
            print("="*60)
            print("You need to log into Facebook first.")
            print("Please run tests/manual_login_test.py to establish a login session,")
            print("then run this test again.")
            print("="*60)
            return
        
        print("📥 Scraping first 3 posts (this may take a moment to scroll and load)...")
        print("⏳ Please wait while we scroll through the Facebook group...")
        
        # Scrape posts (limit to 3) using the original working method
        posts = await scraper.scrape_group_posts(group_url, max_posts=3)
        
        if not posts:
            print("❌ No posts found. Make sure:")
            print("   • You're logged into Facebook")
            print("   • The group URL is correct")
            print("   • The group is accessible")
            print("   • The group has recent posts")
            return
            
        if len(posts) < 3:
            print(f"⚠️  Found only {len(posts)} posts (requested 3)")
            print("   • This group might have fewer recent posts")
            print("   • Analyzing the available posts...")
        
        print(f"✅ Found {len(posts)} posts")
        
        # Save scraped posts to file
        print(f"\n💾 SAVING SCRAPED POSTS")
        print("=" * 40)
        scraped_file_path = save_scraped_posts(posts, group_url)
        print("\n" + "=" * 60)
        print("📊 ANALYSIS RESULTS")
        print("=" * 60)
        
        # Analyze each post
        match_count = 0
        no_match_count = 0
        posts_with_analysis = []  # Store posts with analysis results
        
        for i, post in enumerate(posts, 1):
            print(f"\n📋 POST {i}/{len(posts)}")
            print("-" * 30)
            print(f"👤 Author: {post.get('author', 'Unknown')}")
            print(f"🏷️  Group: {post.get('group_name', 'Unknown')}")
            print(f"📝 Content: {post.get('content', 'No content')[:150]}...")
            if len(post.get('content', '')) > 150:
                print("    [Content truncated...]")
            
            print(f"🤖 Analyzing with Ollama ({os.getenv('OLLAMA_MODEL', 'llama3.1:latest')})...")
            result = analyzer.analyze_post(post)
            
            # Add analysis result to post data
            post_with_analysis = post.copy()
            post_with_analysis['ollama_result'] = result
            post_with_analysis['analysis_timestamp'] = datetime.now().isoformat()
            posts_with_analysis.append(post_with_analysis)
            
            # Display result with clear formatting
            if result == "match":
                print("🎯 OLLAMA RESULT: ✅ MATCH - This apartment meets the criteria!")
                match_count += 1
            else:
                print("🎯 OLLAMA RESULT: ❌ NO MATCH - This apartment doesn't meet the criteria")
                no_match_count += 1
            
            print(f"🔗 Link: {post.get('link', 'No link')}")
            print(f"⏰ Time: {post.get('timestamp', 'No timestamp')}")
            
        # Summary
        print("\n" + "=" * 60)
        print("📈 SUMMARY")
        print("=" * 60)
        print(f"✅ Matching apartments: {match_count}")
        print(f"❌ Non-matching posts: {no_match_count}")
        print(f"📊 Match rate: {(match_count/len(posts))*100:.1f}%")
        
        # Save Ollama analysis results to file
        print(f"\n🤖 SAVING OLLAMA ANALYSIS RESULTS")
        print("=" * 50)
        ollama_file_path = save_ollama_results(posts_with_analysis, group_url, scraped_file_path)
        
        print(f"\n📁 FILES SAVED:")
        print(f"   📄 Scraped posts: {os.path.basename(scraped_file_path)}")
        print(f"   🤖 Ollama results: {os.path.basename(ollama_file_path)}")
        
        if match_count > 0:
            print("\n🎉 Found suitable apartments! Check the matching posts above.")
        else:
            print("\n⚠️  No suitable apartments found in these posts.")
            print("   The Ollama analyzer correctly filtered out inappropriate listings.")
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Error during scraping: {e}")
        print("\nTroubleshooting tips:")
        print("• Make sure you're logged into Facebook in your browser")
        print("• Verify the group URL is correct and accessible")
        print("• Check your internet connection")
        print("• Ensure Playwright is properly installed")
    finally:
        try:
            print("\n🔄 Cleaning up browser...")
            await scraper.cleanup()
        except:
            pass


def test_with_predefined_groups():
    """Test with the default Israeli rental Facebook group."""
    print("🏠 Testing with default Israeli rental group")
    print("=" * 50)
    
    # Default group
    default_group = "https://www.facebook.com/groups/716258928467864/?sorting_setting=CHRONOLOGICAL"
    
    print("Default group:")
    print(f"1. {default_group}")
    print("   (דירות בשושו פתח תקווה והסביבה)")
    
    # Auto-use default group for testing
    choice = ""
    
    if choice == 'c':
        custom_url = input("Enter Facebook group URL: ").strip()
        if custom_url:
            asyncio.run(test_manual_group_scraping(custom_url))
        else:
            print("❌ No URL provided")
    else:
        # Use default group
        asyncio.run(test_manual_group_scraping(default_group))


if __name__ == "__main__":
    print("🧪 Manual Facebook Group Scraper Test")
    print("=" * 40)
    print("This test will:")
    print("• Scrape the first 3 posts from a Facebook group")
    print(f"• Analyze each post with Ollama ({os.getenv('OLLAMA_MODEL', 'llama3.1:latest')}) for apartment rental criteria")
    print("• Show detailed results for each post")
    print()
    
    choice = input("Choose option:\n1. Use default group (Petah Tikva area)\n2. Enter custom group URL\nChoice (1-2): ").strip()
    
    if choice == "1":
        test_with_predefined_groups()
    elif choice == "2":
        custom_url = input("Enter Facebook group URL: ").strip()
        if custom_url:
            asyncio.run(test_manual_group_scraping(custom_url))
        else:
            print("❌ No URL provided")
    else:
        print("❌ Invalid choice")
