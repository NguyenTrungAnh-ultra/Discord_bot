import os
import gc
import json
from google import genai
from src.modules.deep_research.state import ResearchState
from src.modules.deep_research.db.pgvector_db import VectorDatabase

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
        response = client.models.embed_content(
            model="gemini-embedding-2",
            contents=insight.get("summary", ""),
        )
        embedding = response.embeddings[0].values
    except Exception as e:
        print(f"Error generating embedding for {url}: {e}")
        embedding = None

    if embedding:
        try:
            VectorDatabase.insert_document(
                url=url,
                title=insight.get("title", ""),
                content=insight.get("summary", ""),
                embedding=embedding,
                insight=insight 
            )
        except Exception as e:
            print(f"Error storing document in DB: {e}")

    # Update insights list in state
    current_insights.append(insight)
    
    # RAM Garbage Collection
    del embedding
    gc.collect()

    return {"insights": current_insights}
