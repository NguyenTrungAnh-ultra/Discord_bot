import os
import requests
from dotenv import load_dotenv
from src.core.scraper.browser import get_random_desktop_user_agent

load_dotenv()

from src.config.config_loader import Config

SEARXNG_URL = Config.get("rag", "searxng_url", "http://localhost:8080")

def search_searxng(query, num_results=10):
    """Searches using SearxNG API."""
    try:
        session = requests.Session()
        user_agent = get_random_desktop_user_agent()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/json, text/plain, */*',
        })
        
        response = session.get(
            f"{SEARXNG_URL}/search",
            params={
                "q": query,
                "format": "json",
                "categories": "general",
            },
            timeout=30
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
