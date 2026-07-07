import os
import gc
import json
from google import genai
from src.modules.deep_research.state import ResearchState
from src.core.db.vector import VectorDatabase

def store_node(state: ResearchState):
    """Generates embedding for the insight and stores it in pgvector."""
    insight = state.get("current_insight")
    url = state.get("current_url")
    
    # Lấy danh sách insights hiện có để trả về nếu có lỗi
    current_insights = list(state.get("insights", []))
    
    if not insight or not url:
        return {"insights": current_insights}

    print(f"Storing insight for: {url}")
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    # Generate embedding
    try:
        # Using gemini-embedding-2 (3072 dimensions)
        text_to_embed = insight.get("summary") or insight.get("title") or "No content available"
        text_to_embed = text_to_embed.strip()
        if not text_to_embed:
            text_to_embed = "No content available"
            
        response = client.models.embed_content(
            model="gemini-embedding-2",
            contents=text_to_embed,
        )
        embedding = response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding for {url}: {e}")
        embedding = None

    if embedding:
        try:
            entities = insight.get("entities") or {}
            ticker = None
            publish_date = None
            if isinstance(entities, dict):
                tickers = entities.get("tickers") or entities.get("ticker")
                if isinstance(tickers, list) and tickers:
                    ticker = tickers[0]
                elif isinstance(tickers, str):
                    ticker = tickers
                publish_date = entities.get("publish_date")

            doc_type = insight.get("layer")

            VectorDatabase.insert_document(
                url=url,
                title=insight.get("title", ""),
                content=insight.get("summary", ""),
                embedding=embedding,
                insight=insight,
                layer=insight.get("layer"),
                entities=insight.get("entities"),
                doc_type=doc_type,
                ticker=ticker,
                publish_date=publish_date,
                embedded_by='gemini-embedding-2'
            )
        except Exception as e:
            print(f"Error storing document in DB: {e}")

    # Update insights list in state
    current_insights.append(insight)
    
    # RAM Garbage Collection
    del embedding
    gc.collect()

    return {"insights": current_insights}
