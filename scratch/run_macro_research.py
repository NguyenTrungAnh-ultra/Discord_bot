import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure root directory is in Python path
sys.path.append(os.getcwd())

from src.modules.deep_research.main_graph import create_research_graph

def main():
    load_dotenv()
    
    # Check for GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return

    # Query choice
    query = input("Enter query for macro research (e.g., Lạm phát Việt Nam 2025) [default: Lạm phát Việt Nam 2025]: ").strip()
    if not query:
        query = "Lạm phát Việt Nam 2025"
        
    print(f"\n🚀 Starting Macro Deep Research for query: '{query}'...")
    
    app = create_research_graph()
    
    initial_state = {
        "query": query,
        "search_queries": [],
        "urls": [],
        "current_url": None,
        "current_title": None,
        "current_content": None,
        "current_insight": None,
        "insights": [],
        "db_insights": None,
        "report": "",
        "iteration": 0,
        "max_iterations": 3
    }
    
    try:
        # Run graph
        final_state = asyncio.run(app.ainvoke(initial_state))
        
        print("\n" + "="*80)
        print(f" DEEP RESEARCH REPORT ".center(80, "="))
        print("="*80)
        
        report = final_state.get("report")
        if report:
            print(report)
        else:
            print("❌ No report was generated or an error occurred.")
            
        print("\n" + "="*80)
        print(f"Processed {len(final_state.get('insights', []))} web sources.")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")

if __name__ == "__main__":
    main()
