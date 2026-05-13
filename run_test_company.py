import asyncio
import sys
import os

# Đảm bảo nhận diện được thư mục src
sys.path.append(os.getcwd())

from src.modules.deep_research.company_graph import create_company_graph

async def test_company_research():
    print("=== TEST HỆ THỐNG PHÂN TÍCH DOANH NGHIỆP (MICRO RESEARCH) ===")
    
    # Khởi tạo Graph
    app = create_company_graph()
    
    # Cấu hình State ban đầu
    # is_mock=True giúp chạy test luồng code mà KHÔNG GỌI API LLM (Tiết kiệm token)
    initial_state = {
        "ticker": "FPT",
        "is_mock": True,
        "business_profile": None,
        "financial_data": None,
        "financial_insight": None,
        "final_memo": None
    }
    
    print(f"Bắt đầu chạy kịch bản Mock cho mã: {initial_state['ticker']}...")
    
    # Chạy Graph
    final_state = await app.ainvoke(initial_state)
    
    print("\n" + "="*50)
    print("KẾT QUẢ BÁO CÁO CUỐI CÙNG (FINAL MEMO):")
    print(final_state.get("final_memo"))
    print("="*50)
    print("\nTest hoàn tất! Luồng LangGraph chạy chính xác.")

if __name__ == "__main__":
    asyncio.run(test_company_research())
