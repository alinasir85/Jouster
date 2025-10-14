#!/usr/bin/env python3
"""
Example usage of the LLM Knowledge Extractor API.
Make sure the API is running on http://localhost:8000 before running this script.

Run from project root: python scripts/example_usage.py
"""

import requests

API_BASE_URL = "http://localhost:8000"


def analyze_text(text):
    """Submit text for analysis."""
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        json={"text": text}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def search_analyses(topic):
    """Search for analyses by topic."""
    response = requests.get(
        f"{API_BASE_URL}/search",
        params={"topic": topic}
    )

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def main():
    # Example 1: Analyze a technology article
    print("=== Example 1: Analyzing Technology Article ===")
    tech_article = """
    The rapid advancement of quantum computing represents a paradigm shift in 
    computational power. Tech giants like Google and IBM are racing to achieve 
    quantum supremacy, with recent breakthroughs suggesting we're closer than 
    ever to practical quantum applications. These developments could revolutionize 
    cryptography, drug discovery, and artificial intelligence.
    """

    result = analyze_text(tech_article)
    if result:
        print(f"Summary: {result['summary']}")
        print(f"Topics: {', '.join(result['topics'])}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Keywords: {', '.join(result['keywords'])}")
        print(f"Confidence Score: {result['confidence_score']}")
        print()

    # Example 2: Analyze a news update
    print("=== Example 2: Analyzing News Update ===")
    news_update = """
    Breaking: Major cybersecurity breach affects millions of users worldwide.
    Hackers exploited a zero-day vulnerability in popular software, leading to
    data theft and system compromises. Security experts warn users to update
    their systems immediately and change all passwords as a precaution.
    """

    result = analyze_text(news_update)
    if result:
        print(f"Summary: {result['summary']}")
        print(f"Topics: {', '.join(result['topics'])}")
        print(f"Sentiment: {result['sentiment']}")
        print(f"Keywords: {', '.join(result['keywords'])}")
        print()

    # Example 3: Search for analyses
    print("=== Example 3: Searching for 'security' ===")
    search_results = search_analyses("security")
    if search_results:
        print(f"Found {search_results['total_count']} analyses matching 'security'")
        for analysis in search_results['analyses'][:3]:  # Show first 3
            print(f"- {analysis['summary'][:80]}...")

    # Example 4: Handle edge cases
    print("\n=== Example 4: Testing Edge Cases ===")

    # Empty input
    print("Testing empty input:")
    result = analyze_text("")

    # Very short input
    print("\nTesting very short input:")
    result = analyze_text("Hello world")
    if result:
        print(f"Summary: {result['summary']}")


if __name__ == "__main__":
    main()
