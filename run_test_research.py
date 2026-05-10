import asyncio
import os
from dotenv import load_dotenv
from src.modules.deep_research.main_graph import create_research_graph

# Load environment variables
load_dotenv()

async def main():
    # Verify API Key
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found in environment.")
        return

    graph = create_research_graph()
    
    initial_state = {
        "query": "Thị trường xe điện tại Việt Nam năm 2024 và triển vọng 2025",
        "max_iterations": 3, # Test with 3 URLs to save time/tokens
        "iteration": 0,
        "urls": [],
        "insights": [],
        "report": "",
        "search_queries": []
    }
    
    print(f"Starting Deep Research for query: '{initial_state['query']}'")
    
    async for output in graph.astream(initial_state):
        for key, value in output.items():
            print(f"\n>>> Executed Node: {key}")
            if key == "translator":
                print(f"Search Queries: {value.get('search_queries')}")
            elif key == "searcher":
                print(f"Found {len(value.get('urls', []))} URLs.")
            elif key == "dispatcher":
                print(f"Processing URL: {value.get('current_url')}")
                print(f"Iteration: {value.get('iteration')}")
            elif key == "processor":
                print(f"Extracted Title: {value.get('current_title')}")
            elif key == "storer":
                print(f"Total Insights Collected: {len(value.get('insights', []))}")
            elif key == "reporter":
                print("\n--- FINAL REPORT ---")
                print(value.get("report"))
                print("--------------------")
    
    print("\nDeep Research Completed.")

if __name__ == "__main__":
    asyncio.run(main())
