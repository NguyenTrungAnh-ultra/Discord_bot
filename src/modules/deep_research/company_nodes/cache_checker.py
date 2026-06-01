import json
from src.modules.deep_research.company_state import CompanyState
from src.modules.deep_research.db.pgvector_db import VectorDatabase

def check_cache(state: CompanyState):
    """
    Node 0: Check Database First to see if we already have the profile or financial data.
    """
    ticker = state["ticker"]
    print(f"\n--- Node 0: Checking Cache for {ticker} ---")
    
    # Define keys
    profile_url = f"internal://company_profile/{ticker}"
    # For financial reports, we use a fixed key for now (2026 as per company_storer.py)
    # In a real scenario, this would be based on the current year/quarter
    finance_url = f"internal://financial_report/{ticker}/2026"
    
    new_data = {}
    from_cache = False
    
    # 1. Check Profile
    profile_doc = VectorDatabase.get_document_by_url(profile_url)
    if not (profile_doc and profile_doc.get("insight")):
        print("-> Profile not found by exact URL. Trying metadata fallback...")
        results = VectorDatabase.search_by_metadata(ticker=ticker, doc_type="company_profile", limit=1)
        if results:
            profile_doc = results[0]
            
    if profile_doc and profile_doc.get("insight"):
        print(f"-> Found cached Business Profile for {ticker}")
        new_data["business_profile"] = profile_doc["insight"]
        from_cache = True
        
    # 2. Check Financial Insight
    finance_doc = VectorDatabase.get_document_by_url(finance_url)
    if not (finance_doc and finance_doc.get("insight")):
        print("-> Financial Insight not found by exact URL. Trying metadata fallback for latest...")
        results = VectorDatabase.search_by_metadata(ticker=ticker, doc_type="financial_report", limit=1)
        if results:
            finance_doc = results[0]
            
    if finance_doc and finance_doc.get("insight"):
        print(f"-> Found cached Financial Insight for {ticker}")
        new_data["financial_insight"] = finance_doc["insight"]
        # Also mark as success if data exists
        new_data["financial_data"] = {"status": "success", "source": "cache"}
        from_cache = True

    if from_cache:
        new_data["_profile_from_cache"] = True
        
    return new_data
