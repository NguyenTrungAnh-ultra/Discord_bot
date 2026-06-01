import sys
import os
import json
from datetime import date

# Ensure root directory is in Python path
sys.path.append(os.getcwd())

from src.modules.deep_research.db.pgvector_db import VectorDatabase
from src.modules.deep_research.db.date_utils import parse_publish_date, format_date_display

def print_test_header(title):
    print("\n" + "="*80)
    print(f" {title.upper()} ".center(80, "="))
    print("="*80)

def main():
    print_test_header("Step 1: Cleaning existing test data & preparing")
    
    # We delete test URLs to ensure clean state
    test_urls = [
        "test://company/tcb/profile",
        "test://company/tcb/q3_2024",
        "test://company/fpt/profile",
        "test://macro/inflation_2025"
    ]
    
    for url in test_urls:
        VectorDatabase.execute_query("DELETE FROM research_documents WHERE url = %s", (url,))
    print("Cleaned up existing test documents.")

    print_test_header("Step 2: Inserting mock documents with metadata")
    
    # Generate mock 3072-dimensional embedding
    # Vector A: represents tech / FPT
    emb_fpt = [0.1] * 3072
    # Vector B: represents bank / TCB
    emb_tcb = [0.05] * 3072
    # Vector C: represents macro inflation
    emb_macro = [-0.02] * 3072

    documents = [
        {
            "url": "test://company/tcb/profile",
            "title": "TCB Core Business Profile",
            "content": "Techcombank business model is focused on retail banking and digital transaction dominance. Moat is high scaling and brand equity.",
            "embedding": emb_tcb,
            "insight": {
                "report_date": "2024",
                "business_model": {"what_they_sell": "Retail banking", "target_customers": "Mass affluent"},
                "economic_moat": {"moat_type": "Scale/Brand", "strength": "High"}
            },
            "layer": "MICRO",
            "entities": {"tickers": ["TCB"], "type": "core_profile"},
            "doc_type": "company_profile",
            "ticker": "TCB",
            "publish_date": "2024" # should parse to 2024-12-31
        },
        {
            "url": "test://company/tcb/q3_2024",
            "title": "TCB Q3 2024 Financial Report Analysis",
            "content": "TCB reported strong Q3 profit before tax growth. Net interest margin stabilized at 4.2%. Debt-to-equity ratio remains extremely low.",
            "embedding": emb_tcb,
            "insight": {
                "report_date": "Q3/2024",
                "health_score": "8.5",
                "key_metrics": {"gross_margin": "4.2% NIM", "cfo": "Positive"}
            },
            "layer": "MICRO",
            "entities": {"tickers": ["TCB"], "type": "financial_data"},
            "doc_type": "financial_report",
            "ticker": "TCB",
            "publish_date": "Q3/2024" # should parse to 2024-09-30
        },
        {
            "url": "test://company/fpt/profile",
            "title": "FPT Corp Technology Business Profile",
            "content": "FPT is the largest technology group in Vietnam. Focuses on software outsourcing, Cloud services, and AI chips investment.",
            "embedding": emb_fpt,
            "insight": {
                "report_date": "15/10/2024",
                "business_model": {"what_they_sell": "IT outsourcing and Cloud"},
                "economic_moat": {"moat_type": "Cost benefit/Labor scale"}
            },
            "layer": "MICRO",
            "entities": {"tickers": ["FPT"], "type": "core_profile"},
            "doc_type": "company_profile",
            "ticker": "FPT",
            "publish_date": "15/10/2024" # should parse to 2024-10-15
        },
        {
            "url": "test://macro/inflation_2025",
            "title": "Vietnam Macroeconomic Inflation 2025 Outlook",
            "content": "Inflation in 2025 is projected to hover around 3.5-4.0% depending on oil price movements and CPI calculations.",
            "embedding": emb_macro,
            "insight": {
                "publish_date": "Q1/2025",
                "summary": "Inflation projection is stable at 3.5%"
            },
            "layer": "MACRO",
            "entities": {"macro_factors": ["Inflation", "CPI"]},
            "doc_type": "macro",
            "ticker": None,
            "publish_date": "Q1/2025" # should parse to 2025-03-31 (using fallback or direct)
        }
    ]

    for doc in documents:
        print(f"Inserting: {doc['title']}")
        VectorDatabase.insert_document(
            url=doc["url"],
            title=doc["title"],
            content=doc["content"],
            embedding=doc["embedding"],
            insight=doc["insight"],
            layer=doc["layer"],
            entities=doc["entities"],
            doc_type=doc["doc_type"],
            ticker=doc["ticker"],
            publish_date=doc["publish_date"]
        )

    print("\nVerification of DB insertion:")
    for url in test_urls:
        doc = VectorDatabase.get_document_by_url(url)
        if doc:
            parsed_d = format_date_display(doc.get("publish_date"))
            ticker_val = doc.get('ticker') or 'None'
            doc_type_val = doc.get('doc_type') or 'None'
            print(f"  URL: {url:<30} | Ticker: {ticker_val:<5} | Type: {doc_type_val:<20} | Parsed Publish Date: {parsed_d}")
        else:
            print(f"  URL: {url:<30} | FAILED TO INSERT!")

    print_test_header("Step 3: Testing metadata-only search (search_by_metadata)")
    
    # 1. Get latest profile for TCB
    print("Querying latest profile for TCB...")
    res_prof = VectorDatabase.search_by_metadata(ticker="TCB", doc_type="company_profile", limit=1)
    if res_prof:
        p = res_prof[0]
        print(f"  SUCCESS! Title: {p['title']} | Date: {format_date_display(p['publish_date'])}")
    else:
        print("  FAILED to find TCB profile!")

    # 2. Get latest financial report for TCB
    print("Querying latest financial report for TCB...")
    res_fin = VectorDatabase.search_by_metadata(ticker="TCB", doc_type="financial_report", limit=1)
    if res_fin:
        f = res_fin[0]
        print(f"  SUCCESS! Title: {f['title']} | Date: {format_date_display(f['publish_date'])}")
    else:
        print("  FAILED to find TCB financial report!")

    # 3. Get all latest documents for ticker TCB
    print("Querying all documents for TCB...")
    res_all = VectorDatabase.search_by_metadata(ticker="TCB", limit=5)
    for idx, r in enumerate(res_all):
        print(f"  [{idx+1}] Title: {r['title']} | Type: {r['doc_type']} | Date: {format_date_display(r['publish_date'])}")

    print_test_header("Step 4: Testing filtered pgvector similarity search (search_with_filters)")

    # Target Query Embedding matching Bank / TCB (emb_tcb)
    query_emb = [0.045] * 3072

    print("Test 4.1: General search (no filters, similarity threshold 0.5)")
    gen_search = VectorDatabase.search_with_filters(query_emb, limit=5, min_similarity=0.5)
    print(f"Found {len(gen_search)} results:")
    for idx, r in enumerate(gen_search):
        ticker_val = r['ticker'] or 'None'
        print(f"  [{idx+1}] Sim: {r['similarity']:.4f} | Ticker: {ticker_val} | Title: {r['title']}")

    print("\nTest 4.2: Ticker filtered search (ticker='TCB')")
    tcb_search = VectorDatabase.search_with_filters(query_emb, ticker="TCB", limit=5, min_similarity=0.3)
    print(f"Found {len(tcb_search)} results:")
    for idx, r in enumerate(tcb_search):
        ticker_val = r['ticker'] or 'None'
        print(f"  [{idx+1}] Sim: {r['similarity']:.4f} | Ticker: {ticker_val} | Title: {r['title']}")

    print("\nTest 4.3: Date range filtered search (publish_date between '01/01/2024' and '01/10/2024')")
    date_search = VectorDatabase.search_with_filters(query_emb, start_date="01/01/2024", end_date="01/10/2024", limit=5, min_similarity=0.3)
    print(f"Found {len(date_search)} results:")
    for idx, r in enumerate(date_search):
        print(f"  [{idx+1}] Sim: {r['similarity']:.4f} | Date: {format_date_display(r['publish_date'])} | Title: {r['title']}")

    # Clean up test rows
    print_test_header("Step 5: Cleaning up test data")
    for url in test_urls:
        VectorDatabase.execute_query("DELETE FROM research_documents WHERE url = %s", (url,))
    print("Database test rows removed. Database is clean!")
    print("Test completed successfully.")

if __name__ == "__main__":
    main()
