import os
import requests
from dotenv import load_dotenv

load_dotenv()

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8080")

def search_searxng(query, num_results=10):
    """Searches using SearxNG API."""
    try:
        response = requests.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "categories": "general",
            },
            timeout=10
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {"url": r["url"], "title": r["title"], "content": r.get("content", "")}
            for r in results[:num_results]
        ]
    except Exception as e:
        print(f"SearxNG search error: {e}")
        return []
