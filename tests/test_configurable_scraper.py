#!/usr/bin/env python3
"""
Test scraper that scrapes X posts from a test Facebook group and analyzes them.

This test uses separate environment variables for configuration:
- TEST_FB_GROUP_URL: The Facebook group URL to test with
- TEST_MAX_POSTS: Maximum number of posts to scrape for testing

Results are saved to:
- test_outputs/scraped_posts/: Raw scraped posts
- test_outputs/ollama_posts/: Analysis results with match/no match
"""

import asyncio
import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv

# Add the src directory to Python path (before local imports)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Load environment variables
load_dotenv()

# Now import local modules
from analyzer import ApartmentAnalyzer  # noqa: E402
from scraper import FacebookScraper  # noqa: E402


class FacebookTestScraper:
    """Test scraper for Facebook groups with configurable parameters."""

    def __init__(self):
        """Initialize the test scraper with environment configuration."""
        # Test-specific environment variables
        self.test_group_url = os.getenv("TEST_FB_GROUP_URL")
        self.test_max_posts = int(os.getenv("TEST_MAX_POSTS", "5"))

        # Validate required configuration
        if not self.test_group_url:
            raise ValueError("TEST_FB_GROUP_URL environment variable is required")

        # Initialize analyzer
        try:
            self.analyzer = ApartmentAnalyzer()
        except ValueError as e:
            print(f"❌ Analyzer initialization failed: {e}")
            raise

        # Create output directories
        self.scraped_output_dir = os.path.join(
            os.path.dirname(__file__), "..", "test_outputs", "scraped_posts"
        )
        self.ollama_output_dir = os.path.join(
            os.path.dirname(__file__), "..", "test_outputs", "ollama_posts"
        )

        os.makedirs(self.scraped_output_dir, exist_ok=True)
        os.makedirs(self.ollama_output_dir, exist_ok=True)

        print("🧪 Facebook Test Scraper Initialized")
        print(f"📍 Test Group: {self.test_group_url}")
        print(f"📊 Max Posts: {self.test_max_posts}")
        print(f"🤖 Model: {self.analyzer.model_name}")

    async def scrape_test_posts(self):
        """Scrape posts from the test Facebook group."""
        print(f"\n🔄 Starting to scrape {self.test_max_posts} posts from test group...")

        try:
            # Force visible browser for login (like manual test)
            print("🖥️  Running in VISIBLE mode for login verification")

            async with FacebookScraper() as scraper:
                await scraper.initialize_browser()

                # Navigate to Facebook first (like manual test does)
                print("🌐 Navigating to Facebook...")
                await scraper.page.goto("https://www.facebook.com", timeout=30000)
                await scraper.page.wait_for_timeout(3000)  # Wait 3 seconds

                # Check current URL to see if logged in (like manual test)
                current_url = scraper.page.url
                print(f"Current page: {current_url}")

                # If we're on facebook.com (not login page), we're likely logged in
                if "facebook.com" in current_url and "login" not in current_url.lower():
                    print("✅ Appears to be logged in!")
                    is_logged_in = True
                else:
                    print("❌ Not logged in - please log into Facebook in your main browser first")
                    is_logged_in = False

                if not is_logged_in:
                    return []

                # Scrape the posts using the scraper instance
                posts = await scraper.scrape_group_posts(self.test_group_url, self.test_max_posts)

            print(f"✅ Successfully scraped {len(posts)} posts")

            # Save raw scraped posts
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Extract group ID from URL for filename
            group_id = self.test_group_url.split('/')[-1].split('?')[0] if '/' in self.test_group_url else "unknown"

            scraped_filename = f"test_scraped_posts_{group_id}_{timestamp}.json"
            scraped_filepath = os.path.join(self.scraped_output_dir, scraped_filename)

            # Prepare data for JSON serialization
            posts_for_json = []
            for post in posts:
                post_data = {
                    "id": post.get("id", "unknown"),
                    "author": post.get("author", "unknown"),
                    "content": post.get("content", ""),
                    "group_name": post.get("group_name", "unknown"),
                    "timestamp": post.get("timestamp", ""),
                    "link": post.get("link", "")
                }
                posts_for_json.append(post_data)

            # Save scraped posts
            with open(scraped_filepath, 'w', encoding='utf-8') as f:
                json.dump({
                    "scrape_info": {
                        "timestamp": datetime.now().isoformat(),
                        "group_url": self.test_group_url,
                        "requested_posts": self.test_max_posts,
                        "actual_posts": len(posts),
                        "model_used": self.analyzer.model_name
                    },
                    "posts": posts_for_json
                }, f, ensure_ascii=False, indent=2)

            print(f"💾 Raw posts saved to: {scraped_filepath}")

            return posts

        except Exception as e:
            print(f"❌ Error during scraping: {e}")
            raise

    def analyze_posts(self, posts):
        """Analyze posts using the apartment analyzer."""
        print(f"\n🤖 Analyzing {len(posts)} posts with Ollama...")

        # Test Ollama connection first
        if not self.analyzer.test_ollama_connection():
            print("❌ Cannot connect to Ollama. Make sure it's running.")
            return None

        analyzed_posts = []
        match_count = 0
        no_match_count = 0

        for i, post in enumerate(posts, 1):
            print(f"\n📋 Analyzing Post {i}/{len(posts)}")
            print(f"👤 Author: {post.get('author', 'Unknown')}")
            print(f"📝 Content: {post.get('content', '')[:100]}...")

            # Analyze the post
            try:
                result = self.analyzer.analyze_post(post)

                # Create analyzed post data
                analyzed_post = {
                    "post_number": i,
                    "original_post": {
                        "id": post.get("id", "unknown"),
                        "author": post.get("author", "unknown"),
                        "content": post.get("content", ""),
                        "group_name": post.get("group_name", "unknown"),
                        "timestamp": post.get("timestamp", ""),
                        "link": post.get("link", "")
                    },
                    "analysis": {
                        "result": result,
                        "model_used": self.analyzer.model_name,
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                }

                analyzed_posts.append(analyzed_post)

                # Count matches
                if result == "match":
                    match_count += 1
                    print("🎯 Result: ✅ MATCH - This apartment meets the criteria!")
                else:
                    no_match_count += 1
                    print("🎯 Result: ❌ NO MATCH - This post doesn't meet the criteria")

            except Exception as e:
                print(f"⚠️ Error analyzing post {i}: {e}")
                analyzed_post = {
                    "post_number": i,
                    "original_post": post,
                    "analysis": {
                        "result": "error",
                        "error": str(e),
                        "model_used": self.analyzer.model_name,
                        "analysis_timestamp": datetime.now().isoformat()
                    }
                }
                analyzed_posts.append(analyzed_post)

        # Save analysis results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        group_id = self.test_group_url.split('/')[-1].split('?')[0] if '/' in self.test_group_url else "unknown"

        ollama_filename = f"test_analysis_results_{group_id}_{timestamp}.json"
        ollama_filepath = os.path.join(self.ollama_output_dir, ollama_filename)

        analysis_summary = {
            "analysis_info": {
                "timestamp": datetime.now().isoformat(),
                "group_url": self.test_group_url,
                "total_posts": len(posts),
                "model_used": self.analyzer.model_name,
                "match_count": match_count,
                "no_match_count": no_match_count,
                "match_rate": (match_count / len(posts)) * 100 if posts else 0
            },
            "analyzed_posts": analyzed_posts
        }

        with open(ollama_filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_summary, f, ensure_ascii=False, indent=2)

        print(f"\n🤖 Analysis results saved to: {ollama_filepath}")

        return analysis_summary

    def display_summary(self, analysis_summary):
        """Display a summary of the analysis results."""
        if not analysis_summary:
            return

        info = analysis_summary["analysis_info"]

        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"📍 Group: {info['group_url']}")
        print(f"📋 Total Posts Analyzed: {info['total_posts']}")
        print(f"🤖 Model Used: {info['model_used']}")
        print(f"✅ Matching Posts: {info['match_count']}")
        print(f"❌ Non-matching Posts: {info['no_match_count']}")
        print(f"📊 Match Rate: {info['match_rate']:.1f}%")

        # Show details for matching posts
        matching_posts = [
            post for post in analysis_summary["analyzed_posts"]
            if post["analysis"]["result"] == "match"
        ]

        if matching_posts:
            print("\n🎯 MATCHING POSTS DETAILS:")
            print("-" * 40)
            for post in matching_posts:
                print(f"📋 Post #{post['post_number']}")
                print(f"   👤 Author: {post['original_post']['author']}")
                print(f"   📝 Content: {post['original_post']['content'][:100]}...")
                print(f"   🔗 Link: {post['original_post']['link'] or 'No link'}")
                print()

        print("📁 Files saved in test_outputs/:")
        print("   📄 Scraped posts: scraped_posts/")
        print("   🤖 Analysis results: ollama_posts/")

    async def run_test(self):
        """Run the complete test: scrape and analyze posts."""
        print("\n🧪 Starting Facebook Group Test")
        print("="*60)

        try:
            # Step 1: Scrape posts
            posts = await self.scrape_test_posts()

            if not posts:
                print("❌ No posts were scraped. Test cannot continue.")
                return False

            # Step 2: Analyze posts
            analysis_summary = self.analyze_posts(posts)

            if not analysis_summary:
                print("❌ Analysis failed. Check Ollama connection.")
                return False

            # Step 3: Display summary
            self.display_summary(analysis_summary)

            print("\n🎉 Test completed successfully!")
            return True

        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False


async def main():
    """Main function to run the test."""
    print("🧪 Facebook Group Test Scraper")
    print("="*60)
    print("This test will:")
    print("• Scrape posts from TEST_FB_GROUP_URL")
    print("• Analyze up to TEST_MAX_POSTS posts")
    print("• Show which posts match apartment criteria")
    print("• Save results to test_outputs/ folders")
    print()

    # Check environment variables
    test_group = os.getenv("TEST_FB_GROUP_URL")
    test_max_posts = os.getenv("TEST_MAX_POSTS", "5")
    ollama_model = os.getenv("OLLAMA_MODEL")

    print("📋 Configuration:")
    print(f"   TEST_FB_GROUP_URL: {test_group or '❌ NOT SET'}")
    print(f"   TEST_MAX_POSTS: {test_max_posts}")
    print(f"   OLLAMA_MODEL: {ollama_model or '❌ NOT SET'}")
    print()

    if not test_group:
        print("❌ Please set TEST_FB_GROUP_URL in your .env file")
        print("   Example: TEST_FB_GROUP_URL=https://www.facebook.com/groups/your-group-id")
        return False

    if not ollama_model:
        print("❌ Please set OLLAMA_MODEL in your .env file")
        print("   Example: OLLAMA_MODEL=llama3.1:latest")
        return False

    try:
        # Initialize and run test
        scraper = FacebookTestScraper()
        success = await scraper.run_test()

        return success

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")
        sys.exit(1)
