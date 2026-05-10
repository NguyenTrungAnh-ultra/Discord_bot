from src.modules.deep_research.state import ResearchState

def dispatch_node(state: ResearchState):
    """Pops the next URL from the list to be processed."""
    urls = list(state.get("urls", []))
    if not urls:
        return {"current_url": None}
    
    current_url = urls.pop(0)
    return {
        "urls": urls,
        "current_url": current_url,
        "iteration": state["iteration"] + 1
    }
