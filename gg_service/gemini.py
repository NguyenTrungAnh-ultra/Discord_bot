import os
from google import genai
from google.genai import types

async def tomtat100(artical):
    # 1. Khởi tạo Client
    client = genai.Client(
        api_key=os.getenv("GEMINI_API_KEY"),

    )

    model = "gemini-flash-latest"

    user_input = f"Tóm tắt bài báo này với tổng số từ là từ 100 đến 200 từ hoặc ngắn hơn nếu cần thiết\
          theo cấu trúc từng ý với mỗi ý đánh dấu là 1 số, ví dụ:\n\
            1.ý thứ nhất: tóm tắt ý thứ nhất\n\
            2.ý thứ hai: tóm tắt ý thứ hai\n\
            tương tự với tất cả cá ý còn lại\n\
            Đây là bài báo:\n'{artical}'"

    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=user_input),
            ],
        ),
    ]

    # 3. Cấu hình Công cụ (Google Search)
    tools = [
        types.Tool(google_search=types.GoogleSearch()), # Đã sửa thành snake_case đúng chuẩn Python SDK
    ]

    # 4. Cấu hình tạo nội dung (Đã sửa lỗi cú pháp)
    # Lưu ý: thinking_config chỉ hoạt động trên một số model nhất định (thường là model Experimental)
    generate_content_config = types.GenerateContentConfig(
        tools=tools,
        # Nếu model hỗ trợ thinking, bỏ comment dòng dưới. Nếu dùng Flash thường thì nên bỏ qua.
        # thinking_config={'thinking_budget': -1}, 
    )

    print("Đang trả lời...\n")
    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text

if __name__ == "__main__":
    api_key=os.getenv("GEMINI_API_KEY")
    print(api_key)
