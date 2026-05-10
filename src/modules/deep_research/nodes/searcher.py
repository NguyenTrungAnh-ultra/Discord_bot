from src.modules.deep_research.state import ResearchState
from src.modules.deep_research.tools.searxng_api import search_searxng

def search_node(state: ResearchState):
    """Performs search for each query and aggregates URLs."""
    all_urls = list(state.get("urls", []))
    for i, q in enumerate(state["search_queries"]):
        print(f"🔍 Searching ({i+1}/{len(state['search_queries'])}): {q}")
        results = search_searxng(q, num_results=5)
        for r in results:
            if r["url"] not in all_urls:
                all_urls.append(r["url"])
    
    return {"urls": all_urls}
