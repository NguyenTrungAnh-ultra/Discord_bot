from typing import TypedDict, List, Optional

class ResearchState(TypedDict):
    query: str
    search_queries: List[str]
    urls: List[str]
    current_url: Optional[str]
    current_title: Optional[str]
    current_content: Optional[str]
    current_insight: Optional[dict]
    insights: List[dict]
    db_insights: Optional[List[dict]] # Past insights from pgvector DB
    report: str
    iteration: int
    max_iterations: int
