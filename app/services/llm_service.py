import json
import logging
import os
from typing import Dict

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set. "
                "Please create a .env file in the project root with OPENAI_API_KEY=your-key-here"
            )
        self.client = OpenAI(api_key=self.api_key)

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze text using OpenAI API to extract summary and metadata.
        
        Args:
            text: The input text to analyze
        
        Returns:
            Dictionary containing summary, title, topics, and sentiment
        
        Raises:
            Exception: If LLM API fails
        """
        try:
            # Create the prompt for structured output
            prompt = f"""Analyze the following text and provide:
1. A 1-2 sentence summary
2. A title (if one can be inferred, otherwise null)
3. Exactly 3 key topics
4. The overall sentiment (positive, neutral, or negative)

Return the result as valid JSON in this exact format:
{{
    "summary": "Your 1-2 sentence summary here",
    "title": "Title here or null",
    "topics": ["topic1", "topic2", "topic3"],
    "sentiment": "positive/neutral/negative"
}}

Text to analyze:
{text[:2000]}  # Limit text length to avoid token limits
"""

            response = self.client.chat.completions.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[
                    {"role": "system",
                     "content": "You are a helpful assistant that analyzes text and returns structured JSON data."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            # Parse the response
            result_text = response.choices[0].message.content.strip()

            # Try to extract JSON from the response
            try:
                # Find JSON in the response (in case there's extra text)
                start_idx = result_text.find('{')
                end_idx = result_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = result_text[start_idx:end_idx]
                    result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to parse LLM response as JSON: {result_text}")
                # Provide fallback response
                return {
                    "summary": "Unable to generate summary due to parsing error.",
                    "title": None,
                    "topics": ["unknown", "error", "parsing"],
                    "sentiment": "neutral"
                }

            # Validate and clean the result
            return self._validate_result(result)

        except Exception as e:
            # Check for specific OpenAI errors
            error_message = str(e)
            if "authentication" in error_message.lower():
                logger.error("OpenAI API authentication failed")
                raise Exception("LLM API authentication failed. Please check your API key.")
            elif "rate limit" in error_message.lower():
                logger.error("OpenAI API rate limit exceeded")
                raise Exception("LLM API rate limit exceeded. Please try again later.")
            elif "api" in error_message.lower():
                logger.error(f"OpenAI API error: {error_message}")
                raise Exception(f"LLM API error: {error_message}")
            else:
                logger.error(f"Unexpected error in LLM service: {error_message}")
                raise Exception(f"LLM analysis failed: {error_message}")

    def _validate_result(self, result: Dict) -> Dict:
        """
        Validate and clean the LLM result to ensure it matches expected format.
        """
        validated = {
            "summary": result.get("summary", "No summary available."),
            "title": result.get("title"),
            "topics": result.get("topics", ["unknown", "unknown", "unknown"]),
            "sentiment": result.get("sentiment", "neutral")
        }

        # Ensure topics is a list of exactly 3 items
        if not isinstance(validated["topics"], list):
            validated["topics"] = ["unknown", "unknown", "unknown"]
        elif len(validated["topics"]) < 3:
            validated["topics"].extend(["unknown"] * (3 - len(validated["topics"])))
        elif len(validated["topics"]) > 3:
            validated["topics"] = validated["topics"][:3]

        # Ensure sentiment is valid
        if validated["sentiment"] not in ["positive", "neutral", "negative"]:
            validated["sentiment"] = "neutral"

        # Convert empty string title to None
        if validated["title"] == "":
            validated["title"] = None

        return validated
