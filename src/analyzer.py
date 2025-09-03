#!/usr/bin/env python3
"""Apartment post analyzer using Ollama LLM."""

import logging
import os
import ollama
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ApartmentAnalyzer:
    """Analyzes apartment posts using Ollama LLM to match rental criteria."""

    def __init__(self, model_name: str = None, ollama_host: str = None, exclude_words: list = None):
        """Initialize the analyzer with Ollama configuration and optional exclude words."""
        self.model_name = model_name or os.getenv("OLLAMA_MODEL")
        if not self.model_name:
            raise ValueError("OLLAMA_MODEL environment variable is required")
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.client = ollama.Client(host=self.ollama_host)
        
        # Set up exclude words from parameter or environment variable
        self.exclude_words = exclude_words or []
        env_exclude_words = os.getenv("ANALYZER_EXCLUDE_WORDS")
        if env_exclude_words:
            # Parse comma-separated exclude words from environment
            env_words = [word.strip() for word in env_exclude_words.split(",") if word.strip()]
            self.exclude_words.extend(env_words)
        
        # Remove duplicates (no need to convert to lowercase for Hebrew)
        self.exclude_words = list(set(self.exclude_words))
        
        if self.exclude_words:
            logger.info(f"Initialized with exclude words: {self.exclude_words}")
    
    def _contains_exclude_words(self, content: str) -> bool:
        """Check if content contains any exclude words."""
        if not self.exclude_words:
            return False
            
        for word in self.exclude_words:
            if word in content:
                logger.info(f"Post excluded due to word: '{word}'")
                return True
        return False
        
    def create_analysis_prompt(self, post_content: str, author: str) -> str:
        """Create an English prompt for apartment analysis with Hebrew content."""
        prompt = f"""Analyze this Hebrew apartment post:

"{post_content}"

Check these criteria strictly:

1. POST TYPE - Is this a rental listing or someone searching?
   - If contains "מחפש", "מחפשים", "מחפשות", "מחפשת" (searching) = FAIL ✗
   - If contains "שותפים", "שותפות", "שותפה", "שותף" (any roommate/partner reference) = FAIL ✗
   - If contains "דרוש", "דרושה", "דרושים", "דרושות" (needed/wanted) = FAIL ✗
   - If contains "עם שותף", "עם שותפה", "עם שותפים", "עם שותפות" (with partners) = FAIL ✗
   - If contains "להשכרה", "משכיר", "דירה להשכרה", "שכירות" (offering rental) = PASS ✓
   - If no clear indication = PASS ✓ (default)

2. PURPOSE - Is it for rent?
   - If mentions "להשכרה" (for rent) = PASS ✓
   - If mentions "למכירה" (for sale) = FAIL ✗
   - If no purpose mentioned = PASS ✓ (default)

3. ROOMS - Is it 2.5+ rooms?
   - 1 room (חדר אחד) = FAIL ✗
   - 1.5 rooms (חדר וחצי) = FAIL ✗  
   - 2 rooms (2 חדרים) = FAIL ✗
   - 2.5 rooms (2.5 חדרים) = PASS ✓
   - 3 rooms (3 חדרים) = PASS ✓
   - 3.5+ rooms (3.5 חדרים ומעלה) = PASS ✓
   - No room count mentioned = FAIL ✗

4. PRICE - Is it within budget (5900 or less)?
   - 5900 or below = PASS ✓
   - Above 5900 = FAIL ✗
   - No price mentioned = PASS ✓ (default)

DECISION RULES:
- If POST TYPE fails (searching, roommate/partner posts) = "no match"
- If ROOMS requirement fails = "no match"
- If ROOMS passes but PURPOSE or PRICE fails = "no match" 
- If all criteria pass/default = "match"

IMPORTANT: Any mention of roommates/partners (שותף/שותפה/שותפים/שותפות) automatically = "no match"

Answer (only "match" or "no match"):"""
        
        return prompt

    def analyze_post(self, post: Dict[str, Any]) -> str:
        """Analyze a single post and return match level."""
        try:
            content = post.get('content', '')
            author = post.get('author', '')
            
            if not content.strip():
                logger.warning("Empty post content")
                return "no match"
            
            # Pre-filter: Check for exclude words before sending to LLM
            if self._contains_exclude_words(content):
                logger.info(f"Post pre-filtered due to exclude words: {content[:50]}...")
                return "no match"
                
            prompt = self.create_analysis_prompt(content, author)
            
            logger.info(f"Analyzing post with LLM: {content[:50]}...")
            
            # Call Ollama synchronously
            response = self.client.chat(
                model=self.model_name,
                messages=[
                    {
                        'role': 'user', 
                        'content': prompt
                    }
                ],
                options={
                    'temperature': 0.0,  # Zero temperature for maximum consistency
                    'top_p': 0.1,        # Very focused responses
                    'max_tokens': 10,    # Short responses only
                    'seed': 12345        # Fixed seed for consistency
                }
            )
            
            result = response['message']['content'].strip().lower()
            logger.info(f"Ollama response: {result}")
            
            # Parse the response for binary classification
            if "match" in result and "no match" not in result:
                return "match"
            else:
                return "no match"
                
        except Exception as e:
            logger.error(f"Error analyzing post: {e}")
            return "no match"  # Conservative fallback

    def analyze_posts(self, posts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Analyze multiple posts and add match level to each."""
        logger.info(f"Analyzing {len(posts)} posts")
        
        analyzed_posts = []
        
        for i, post in enumerate(posts):
            logger.info(f"Processing post {i+1}/{len(posts)}")
            
            match_level = self.analyze_post(post)
            
            # Add analysis result to post
            analyzed_post = post.copy()
            analyzed_post['match_level'] = match_level
            analyzed_posts.append(analyzed_post)
            
            logger.info(f"Post {i+1} classified as: {match_level}")
            
        logger.info(f"Finished analyzing {len(analyzed_posts)} posts")
        return analyzed_posts
        
    def test_ollama_connection(self) -> bool:
        """Test if Ollama is running and the model is available."""
        try:
            # Try to list models to test connection
            models_response = self.client.list()
            
            # Extract model names from the response
            model_names = [model.model for model in models_response.models]
            
            # Check if our model is available
            model_found = False
            for model_name in model_names:
                if self.model_name in model_name or model_name.startswith(self.model_name.split(':')[0]):
                    model_found = True
                    break
            
            if model_found:
                logger.info(f"✅ Ollama connection successful, model {self.model_name} is available")
                return True
            else:
                logger.warning(f"⚠️ Model {self.model_name} not found. Available models: {model_names}")
                logger.info("Trying to pull the model...")
                # Try to pull the model
                self.client.pull(self.model_name)
                logger.info(f"✅ Successfully pulled model {self.model_name}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Failed to connect to Ollama: {e}")
            logger.error("Make sure Ollama is running with: ollama serve")
            return False

    def get_match_posts(self, posts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Filter posts to return only those with match classification."""
        logger.info(f"Filtering {len(posts)} posts for matches")
        
        # Analyze all posts first
        analyzed_posts = self.analyze_posts(posts)
        
        # Filter for match posts only 
        match_posts = [
            post for post in analyzed_posts 
            if post.get('match_level') == 'match'
        ]
        
        logger.info(f"Found {len(match_posts)} matching posts out of {len(posts)} total")
        return match_posts

    def filter_posts(self, posts: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
        """Filter posts to return only relevant/matching ones (alias for get_match_posts)."""
        return self.get_match_posts(posts)


# Example usage function
def analyze_facebook_posts(posts: list[Dict[str, Any]], model_name: str = None, exclude_words: list = None) -> list[Dict[str, Any]]:
    """Convenience function to analyze Facebook posts."""
    analyzer = ApartmentAnalyzer(model_name=model_name, exclude_words=exclude_words)
    
    # Test connection first
    if not analyzer.test_ollama_connection():
        logger.error("Cannot connect to Ollama, returning posts without analysis")
        return posts
    
    return analyzer.analyze_posts(posts)
