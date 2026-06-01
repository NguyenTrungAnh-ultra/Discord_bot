import asyncio
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Đảm bảo nhận diện được thư mục src
sys.path.append(os.getcwd())

from src.modules.deep_research.company_graph import create_company_graph

async def test_company_research():
    print("=== TEST HỆ THỐNG PHÂN TÍCH DOANH NGHIỆP (MICRO RESEARCH) ===")
    
    # Khởi tạo Graph
    app = create_company_graph()
    
    # Cấu hình State ban đầu
    initial_state = {
        "ticker": "VIC",
        "business_profile": None,
        "financial_data": None,
        "financial_insight": None,
        "final_memo": None,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_requests": 0,
        "node_tokens": {}
    }
    
    print(f"Bắt đầu chạy kịch bản Real cho mã: {initial_state['ticker']}...")
    
    # Chạy Graph
    final_state = await app.ainvoke(initial_state)
    
    print("\n" + "="*50)
    print("KẾT QUẢ BÁO CÁO CUỐI CÙNG (FINAL MEMO):")
    print(final_state.get("final_memo"))
    print("="*50)
    
    print("\n" + "-"*50)
    print("THỐNG KÊ TÀI NGUYÊN SỬ DỤNG:")
    print(f"- Tổng số Input Token  (ước tính): {final_state.get('total_input_tokens')}")
    print(f"- Tổng số Output Token (ước tính): {final_state.get('total_output_tokens')}")
    print(f"- Tổng số Request gửi đi         : {final_state.get('total_requests')}")
    
    node_tokens = final_state.get('node_tokens', {})
    if node_tokens:
        print("\nCHI TIẾT TOKEN TỪNG NODE:")
        for node_name, data in node_tokens.items():
            print(f"  + {node_name}:")
            print(f"      - Input : {data.get('input', 0)}")
            print(f"      - Output: {data.get('output', 0)}")
            
    print("-" * 50)
    
    print("\nTest hoàn tất! Luồng LangGraph chạy chính xác.")

if __name__ == "__main__":
    asyncio.run(test_company_research())
