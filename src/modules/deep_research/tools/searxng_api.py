import os
import requests
import json
import re
from dotenv import load_dotenv
from google import genai
from google.genai import types
from src.core.scraper.browser import get_random_desktop_user_agent
from src.config.config_loader import Config

load_dotenv()

SEARXNG_URL = Config.get("rag", "searxng_url", "http://localhost:8080")

def search_gemini_fallback(query, num_results=10):
    """Fallback search using Gemini Google Search grounding."""
    try:
        print(f"🔄 [Search Fallback] Local SearxNG returned no results. Querying Gemini Search Grounding for: '{query}'...")
        # Fallback always uses Gemini Client
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        
        prompt = (
            f"Perform a Google Search for: '{query}'. "
            f"Return the top {num_results} most relevant webpage URLs as a raw JSON list of strings (e.g. [\"https://url1\", \"https://url2\"]). "
            f"Do not include any conversational filler, markdown formatting (like ```json), or explanation. Only return the JSON array."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        
        text = response.text.strip()
        # Clean markdown codeblocks if any
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n', '', text)
            text = re.sub(r'\n```$', '', text)
            text = text.strip()
            
        try:
            urls = json.loads(text)
            if isinstance(urls, list):
                print(f"✅ [Search Fallback] Gemini Search retrieved {len(urls)} URLs.")
                return [{"url": url, "title": "Google Search Result", "content": ""} for url in urls[:num_results]]
        except Exception as json_err:
            # If JSON parsing fails, extract URLs using regex
            urls = re.findall(r'https?://[^\s"\'\]]+', text)
            if urls:
                print(f"✅ [Search Fallback] Gemini Search extracted {len(urls)} URLs via regex.")
                return [{"url": url, "title": "Google Search Result", "content": ""} for url in urls[:num_results]]
                
    except Exception as e:
        print(f"❌ [Search Fallback] Gemini Search error: {e}")
    return []

def search_searxng(query, num_results=10):
    """Searches using SearxNG API with optional Gemini fallback."""
    results = []
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
        if results:
            return [
                {"url": r["url"], "title": r["title"], "content": r.get("content", "")}
                for r in results[:num_results]
            ]
    except Exception as e:
        print(f"SearxNG search error: {e}")

    # Fallback check
    if Config.get("rag", "use_gemini_search_fallback", True):
        return search_gemini_fallback(query, num_results)
        
    return []
