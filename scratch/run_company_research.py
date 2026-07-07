import os
import sys
import asyncio
from dotenv import load_dotenv

# Ensure root directory is in Python path
sys.path.append(os.getcwd())

from src.modules.deep_research.company_graph import create_company_graph

def main():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass
    load_dotenv()
    
    # Check for GEMINI_API_KEY
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ Error: GEMINI_API_KEY not found in .env file.")
        return

    # Ticker choice
    ticker = input("Enter ticker to research (e.g., TCB, FPT, HPG) [default: TCB]: ").strip().upper()
    if not ticker:
        ticker = "TCB"
        
    print(f"\n🚀 Starting Company Deep Research for ticker: {ticker}...")
    
    app = create_company_graph()
    
    initial_state = {
        "ticker": ticker,
        "business_profile": None,
        "financial_data": None,
        "financial_insight": None,
        "final_memo": None,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_requests": 0,
        "node_tokens": {}
    }
    
    try:
        # Run graph
        final_state = asyncio.run(app.ainvoke(initial_state))
        
        print("\n" + "="*80)
        print(f" INVESTMENT MEMO FOR {ticker} ".center(80, "="))
        print("="*80)
        
        memo = final_state.get("final_memo")
        if memo:
            print(memo)
        else:
            print("❌ No memo was generated or an error occurred.")
            
        print("\n" + "="*80)
        print(" TOKEN & REQUEST USAGE SUMMARY ".center(80, "="))
        print("="*80)
        print(f"  Total Requests:      {final_state.get('total_requests', 0)}")
        print(f"  Total Input Tokens:  {final_state.get('total_input_tokens', 0)}")
        print(f"  Total Output Tokens: {final_state.get('total_output_tokens', 0)}")
        print(f"  Node breakdown:")
        for node, tokens in final_state.get("node_tokens", {}).items():
            print(f"    - {node}: Input {tokens.get('input', 0)}, Output {tokens.get('output', 0)}")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")

if __name__ == "__main__":
    main()
