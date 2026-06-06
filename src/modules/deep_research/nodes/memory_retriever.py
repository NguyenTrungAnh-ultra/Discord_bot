import os
import re
import gc
from google import genai
from src.modules.deep_research.state import ResearchState
from src.core.db.vector import VectorDatabase
from src.utils.date_parser import format_date_display

def retrieve_memory_node(state: ResearchState):
    """
    Retrieves historically relevant research documents/insights from pgvector database.
    Integrates results into state['db_insights'] for reporter usage.
    """
    query = state.get("query")
    if not query:
        return {"db_insights": []}

    print(f"\n--- Node: Memory Retriever for query: '{query}' ---")
    
    # 1. Check if the query refers to a specific ticker (3 uppercase letters, e.g., HPG, FPT)
    ticker = None
    ticker_matches = re.findall(r'\b([A-Z]{3})\b', query)
    if not ticker_matches:
        # Fallback to search for 3-letter lowercase words and capitalize them if they look like tickers
        words = re.findall(r'\b([a-zA-Z]{3})\b', query)
        for w in words:
            if w.upper() not in ["AND", "FOR", "THE", "VND", "USD"]: # Skip common stop words
                ticker = w.upper()
                break
    else:
        ticker = ticker_matches[0]
        
    # 2. Generate query embedding
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    try:
        response = client.models.embed_content(
            model="gemini-embedding-2",
            contents=query,
        )
        query_embedding = response.embeddings[0].values
    except Exception as e:
        print(f"Error generating query embedding in memory retriever: {e}")
        return {"db_insights": []}

    db_insights = []
    
    # 3. Perform filtered pgvector search
    try:
        if ticker:
            print(f"Memory Retriever: Ticker '{ticker}' detected. Performing filtered search...")
            # First attempt: search with ticker filter
            filtered_results = VectorDatabase.search_with_filters(
                query_embedding=query_embedding,
                ticker=ticker,
                limit=5,
                min_similarity=0.3
            )
            print(f"Memory Retriever: Found {len(filtered_results)} results for ticker {ticker}.")
            db_insights.extend(filtered_results)
            
            # If not enough results, combine with general search
            if len(db_insights) < 3:
                print("Memory Retriever: Insufficient ticker-filtered results. Performing general fallback search...")
                general_results = VectorDatabase.search_with_filters(
                    query_embedding=query_embedding,
                    limit=5 - len(db_insights),
                    min_similarity=0.35
                )
                # Avoid duplicate URLs
                existing_urls = {r.get("url") for r in db_insights}
                for r in general_results:
                    if r.get("url") not in existing_urls:
                        db_insights.append(r)
        else:
            print("Memory Retriever: No specific ticker detected. Performing general similarity search...")
            db_insights = VectorDatabase.search_with_filters(
                query_embedding=query_embedding,
                limit=5,
                min_similarity=0.35
            )
            
        print(f"Memory Retriever: Retrieved {len(db_insights)} historical insights.")
        for idx, insight in enumerate(db_insights):
            title = insight.get("title", "No Title")
            sim = insight.get("similarity", 0.0)
            pub_date = format_date_display(insight.get("publish_date"))
            doc_t = insight.get("doc_type", "N/A")
            tick = insight.get("ticker") or "N/A"
            print(f"  [{idx+1}] Sim: {sim:.4f} | Date: {pub_date} | Ticker: {tick} | Type: {doc_t} | Title: {title}")
            
    except Exception as e:
        print(f"Error executing memory retriever search: {e}")

    # RAM Garbage Collection
    del query_embedding
    gc.collect()

    return {"db_insights": db_insights}
