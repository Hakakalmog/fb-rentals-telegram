import json
import logging
import re
from typing import Any

import requests

logger = logging.getLogger(__name__)


class LLaMAFilter:
  """AI-powered post filtering using local LLaMA model via Ollama."""

  def __init__(
    self,
    ollama_host: str = "http://localhost:11434",
    model_name: str = "llama3.2:3b",
    max_price: int = 2000,
  ):
    """Initialize filter with AI model configuration and filtering rules."""
    self.ollama_host = ollama_host.rstrip("/")
    self.model_name = model_name
    self.max_price = max_price
    self.session = requests.Session()

  def check_ollama_connection(self) -> bool:
    """Check if Ollama is running and accessible."""
    try:
      response = self.session.get(f"{self.ollama_host}/api/tags", timeout=5)
      return response.status_code == 200
    except Exception as e:
      logger.error(f"Cannot connect to Ollama at {self.ollama_host}: {e}")
      return False

  def ensure_model_available(self) -> bool:
    """Ensure the specified model is available in Ollama."""
    try:
      response = self.session.get(f"{self.ollama_host}/api/tags", timeout=10)
      if response.status_code == 200:
        models = response.json().get("models", [])
        model_names = [model["name"] for model in models]

        if self.model_name in model_names:
          return True

        # Try to pull the model if not available
        logger.info(f"Model {self.model_name} not found, attempting to pull...")
        pull_response = self.session.post(
          f"{self.ollama_host}/api/pull",
          json={"name": self.model_name},
          timeout=300,  # 5 minutes timeout for model pull
        )

        return pull_response.status_code == 200

    except Exception as e:
      logger.error(f"Error checking/pulling model: {e}")

    return False

  def extract_price_from_content(self, content: str) -> int | None:
    """Extract price from post content."""
    # Price patterns (more comprehensive)
    price_patterns = [
      r"\$(\d{1,3}(?:,\d{3})*)",  # $1,500
      r"(\d{1,3}(?:,\d{3})*)\s*(?:dollars?|\$)",  # 1500 dollars
      r"(\d+)k",  # 2k
      r"(\d+)\s*thousand",  # 2 thousand
    ]

    for pattern in price_patterns:
      matches = re.findall(pattern, content, re.IGNORECASE)
      for match in matches:
        try:
          # Handle 'k' notation
          if (
            "k"
            in content[
              content.find(match) : content.find(match) + 10
            ].lower()
          ):
            return int(match) * 1000
          elif (
            "thousand"
            in content[
              content.find(match) : content.find(match) + 20
            ].lower()
          ):
            return int(match) * 1000
          else:
            # Remove commas and convert
            return int(match.replace(",", ""))
        except ValueError:
          continue

    return None

  def basic_filter_check(self, post: dict[str, Any]) -> dict[str, Any]:
    """Perform basic filtering before LLM analysis."""
    content = post.get("content", "").lower()
    title = post.get("title", "").lower()
    full_text = f"{title} {content}"

    result = {
      "passes_basic_filter": True,
      "reasons": [],
    }

    # Extract and check price
    price = self.extract_price_from_content(full_text)
    if price:
      if price > self.max_price:
        result["passes_basic_filter"] = False
        result["reasons"].append(
          f"Price ${price} exceeds maximum ${self.max_price}"
        )

    return result

  def create_llm_prompt(
    self, post: dict[str, Any], basic_filter_result: dict[str, Any]
  ) -> str:
    """Create a prompt for LLM analysis."""
    content = post.get("content", "")
    author = post.get("author", "Unknown")

    prompt = f"""
Analyze this Facebook rental post and determine if it's a legitimate rental listing.

POST CONTENT:
{content}

AUTHOR: {author}

Please analyze this post and respond with a JSON object containing:
1. "is_rental": boolean - true if this is a legitimate rental listing
2. "confidence": number between 0-1 indicating confidence in the assessment
3. "reasoning": string explaining the decision
4. "red_flags": array of any red flags or concerns
5. "positive_indicators": array of positive indicators for legitimate rental

Consider these factors:
- Is this actually about renting/housing?
- Does it seem like a scam or spam?
- Are there clear rental terms (price, location, contact info)?
- Does the language seem natural and legitimate?
- Are there any obvious red flags (too good to be true, urgent language, etc.)?

Respond only with valid JSON, no additional text.
"""
    return prompt

  def query_llm(self, prompt: str) -> dict[str, Any] | None:
    """Query the LLM with a prompt."""
    try:
      payload = {
        "model": self.model_name,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "top_p": 0.9, "num_predict": 500},
      }

      response = self.session.post(
        f"{self.ollama_host}/api/generate", json=payload, timeout=60
      )

      if response.status_code == 200:
        result = response.json()
        llm_response = result.get("response", "").strip()

        # Try to parse JSON from the response
        try:
          # Find JSON in the response (in case there's extra text)
          json_start = llm_response.find("{")
          json_end = llm_response.rfind("}") + 1

          if json_start >= 0 and json_end > json_start:
            json_str = llm_response[json_start:json_end]
            return json.loads(json_str)
          else:
            # Fallback: try to parse the entire response
            return json.loads(llm_response)

        except json.JSONDecodeError as e:
          logger.error(f"Failed to parse LLM JSON response: {e}")
          logger.debug(f"LLM response: {llm_response}")
          return None
      else:
        logger.error(f"LLM query failed with status {response.status_code}")
        return None

    except Exception as e:
      logger.error(f"Error querying LLM: {e}")
      return None

  def create_fallback_analysis(
    self, post: dict[str, Any], basic_filter_result: dict[str, Any]
  ) -> dict[str, Any]:
    """Create a fallback analysis when LLM is not available."""
    content = post.get("content", "").lower()

    # Simple heuristics for rental posts
    rental_keywords = [
      "rent",
      "rental",
      "apartment",
      "room",
      "bedroom",
      "bathroom",
      "lease",
      "available",
      "housing",
      "studio",
      "furnished",
      "utilities",
      "deposit",
      "move in",
      "landlord",
      "tenant",
    ]

    spam_indicators = [
      "click here",
      "limited time",
      "act now",
      "guaranteed",
      "make money",
      "work from home",
      "free money",
      "no experience",
    ]

    rental_score = sum(1 for keyword in rental_keywords if keyword in content)
    spam_score = sum(1 for indicator in spam_indicators if indicator in content)

    is_rental = (
      rental_score >= 2
      and spam_score == 0
      and basic_filter_result["passes_basic_filter"]
    )
    confidence = min(0.8, (rental_score * 0.1) + 0.3) if is_rental else 0.2

    return {
      "is_rental": is_rental,
      "confidence": confidence,
      "reasoning": f"Fallback analysis: {rental_score} rental keywords, {spam_score} spam indicators",
      "red_flags": ["Spam indicators found"] if spam_score > 0 else [],
      "positive_indicators": [f"Contains {rental_score} rental keywords"]
      if rental_score > 0
      else [],
    }

  def analyze_post(self, post: dict[str, Any]) -> dict[str, Any]:
    """Analyze a post to determine if it's relevant."""
    try:
      # First, perform basic filtering
      basic_result = self.basic_filter_check(post)

      # If it fails basic filtering, return early
      if not basic_result["passes_basic_filter"]:
        return {
          "is_relevant": False,
          "confidence": 0.9,
          "reasoning": "; ".join(basic_result["reasons"]),
          "filter_type": "basic",
          "basic_filter_result": basic_result,
          "llm_analysis": None,
        }

      # Try LLM analysis
      llm_analysis = None
      if self.check_ollama_connection():
        prompt = self.create_llm_prompt(post, basic_result)
        llm_analysis = self.query_llm(prompt)

      # Use LLM analysis if available, otherwise fallback
      if llm_analysis:
        is_relevant = (
          llm_analysis.get("is_rental", False)
          and llm_analysis.get("confidence", 0) > 0.5
        )

        return {
          "is_relevant": is_relevant,
          "confidence": llm_analysis.get("confidence", 0.5),
          "reasoning": llm_analysis.get("reasoning", "LLM analysis"),
          "filter_type": "llm",
          "basic_filter_result": basic_result,
          "llm_analysis": llm_analysis,
        }
      else:
        # Fallback analysis
        fallback = self.create_fallback_analysis(post, basic_result)

        return {
          "is_relevant": fallback["is_rental"],
          "confidence": fallback["confidence"],
          "reasoning": fallback["reasoning"],
          "filter_type": "fallback",
          "basic_filter_result": basic_result,
          "llm_analysis": fallback,
        }

    except Exception as e:
      logger.error(f"Error analyzing post: {e}")
      return {
        "is_relevant": False,
        "confidence": 0.1,
        "reasoning": f"Error during analysis: {e}",
        "filter_type": "error",
        "basic_filter_result": None,
        "llm_analysis": None,
      }

  def filter_posts(self, posts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter a list of posts for relevance."""
    filtered_posts = []

    for post in posts:
      analysis = self.analyze_post(post)

      if analysis["is_relevant"]:
        # Add analysis results to the post
        post["relevance_score"] = analysis["confidence"]
        post["filter_reasoning"] = analysis["reasoning"]
        post["filter_analysis"] = analysis
        filtered_posts.append(post)

        logger.info(
          f"Post accepted: {post.get('title', 'No title')[:50]}... "
          f"(confidence: {analysis['confidence']:.2f})"
        )
      else:
        logger.debug(
          f"Post rejected: {post.get('title', 'No title')[:50]}... "
          f"Reason: {analysis['reasoning']}"
        )

    # Sort by relevance score
    filtered_posts.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    logger.info(
      f"Filtered {len(filtered_posts)} relevant posts from {len(posts)} total posts"
    )

    return filtered_posts
