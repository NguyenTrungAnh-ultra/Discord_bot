from src.modules.deep_research.state import ResearchState
from src.modules.deep_research.tools.searxng_api import search_searxng
from src.config.config_loader import Config

from urllib.parse import urlparse

def search_node(state: ResearchState):
    """Performs search for each query and aggregates URLs."""
    all_urls = list(state.get("urls", []))
    num_search_results = Config.get("rag", "num_search_results", 5)
    
    social_domains = {
        "facebook.com", "x.com", "reddit.com",
        "youtube.com", "tiktok.com", "instagram.com", "linkedin.com",
        "pinterest.com"
    }
    
    for i, q in enumerate(state["search_queries"]):
        print(f"🔍 Searching ({i+1}/{len(state['search_queries'])}): {q}")
        results = search_searxng(q, num_results=num_search_results)
        for r in results:
            url = r["url"]
            try:
                domain = urlparse(url).netloc.lower()
                if any(sd in domain for sd in social_domains):
                    continue
            except:
                pass
                
            if url not in all_urls:
                all_urls.append(url)
    
    return {"urls": all_urls}
