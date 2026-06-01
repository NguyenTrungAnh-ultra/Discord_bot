import os
import json
from google import genai
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.db.pgvector_db import VectorDatabase
from src.utils.llm_utils import estimate_tokens

async def store_company_data(state: CompanyState):
    """
    Node 3: Lưu trữ dữ liệu phân tích doanh nghiệp vào PostgreSQL (pgvector).
    """
    ticker = state["ticker"]
    print(f"\n--- Node 3: Storing Data for {ticker} ---")
    
    if state.get("_profile_from_cache"):
        print(f"-> Data for {ticker} was retrieved from Cache. Skipping storage Node.")
        return state

    # Khởi tạo counters
    current_input_tokens = state.get("total_input_tokens", 0)
    current_output_tokens = state.get("total_output_tokens", 0)
    current_requests = state.get("total_requests", 0)
    node_tokens = state.get("node_tokens", {})
    node_3_input = 0
    node_3_output = 0

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    # 1. Lưu Profile (Dữ liệu Tĩnh)
    if state.get("business_profile"):
        profile = state["business_profile"]
        content_to_embed = json.dumps(profile.get("business_model", {})) + " " + json.dumps(profile.get("economic_moat", {}))
        
        print(f"Generating embedding for {ticker} business profile...")
        try:
            current_requests += 1
            input_tokens = estimate_tokens(content_to_embed)
            current_input_tokens += input_tokens
            node_3_input += input_tokens

            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=content_to_embed,
            )
            embedding = response.embeddings[0].values
            
            VectorDatabase.insert_document(
                url=f"internal://company_profile/{ticker}",
                title=f"Business Profile: {ticker}",
                content=content_to_embed,
                embedding=embedding,
                insight=profile,
                layer="MICRO",
                entities={"tickers": [ticker], "type": "core_profile"},
                doc_type="company_profile",
                ticker=ticker,
                publish_date=profile.get("report_date")
            )
            print(f"Successfully stored business profile for {ticker}.")
        except Exception as e:
            print(f"Error storing business profile: {e}")

    # 2. Lưu Tài chính (Dữ liệu Động)
    if state.get("financial_insight"):
        insight = state["financial_insight"]
        content_to_embed = insight.get("chain_of_thought", "") + " " + json.dumps(insight.get("key_metrics", {}))
        
        print(f"Generating embedding for {ticker} financial insight...")
        try:
            current_requests += 1
            input_tokens = estimate_tokens(content_to_embed)
            current_input_tokens += input_tokens
            node_3_input += input_tokens

            response = client.models.embed_content(
                model="gemini-embedding-2",
                contents=content_to_embed,
            )
            embedding = response.embeddings[0].values
            # Determine report date from insight, falling back to 2026 if not found
            report_date = insight.get("report_date") or "2026"
            url_friendly_date = str(report_date).replace("/", "_").replace(" ", "_")
            VectorDatabase.insert_document(
                url=f"internal://financial_report/{ticker}/{url_friendly_date}",
                title=f"Financial Analysis {report_date}: {ticker}",
                content=content_to_embed,
                embedding=embedding,
                insight=insight,
                layer="MICRO",
                entities={"tickers": [ticker], "type": "financial_data"},
                doc_type="financial_report",
                ticker=ticker,
                publish_date=report_date
            )
            print(f"Successfully stored financial insight for {ticker}.")
        except Exception as e:
            print(f"Error storing financial insight: {e}")

    node_entry = node_tokens.get("Node_3_Storer", {"input": 0, "output": 0})
    node_tokens["Node_3_Storer"] = {
        "input": node_entry["input"] + node_3_input,
        "output": node_entry["output"] + node_3_output
    }

    return {
        "total_input_tokens": current_input_tokens,
        "total_output_tokens": current_output_tokens,
        "total_requests": current_requests,
        "node_tokens": node_tokens
    }
