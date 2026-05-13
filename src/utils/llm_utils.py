def estimate_tokens(text: str) -> int:
    """
    Ước tính số lượng token dựa trên chiều dài chuỗi.
    Tỉ lệ trung bình: 1 token ~ 3.5 ký tự (phù hợp cho hỗn hợp Việt - Anh).
    """
    if not text:
        return 0
    return len(text) // 3 + 1

def count_response_tokens(response) -> int:
    """
    Lấy số token thực tế từ response của Google GenAI nếu có, 
    nếu không thì ước tính từ text trả về.
    """
    try:
        # Thử lấy từ usage_metadata của Google SDK
        if hasattr(response, 'usage_metadata'):
            return response.usage_metadata.candidates_token_count
    except:
        pass
    
    if hasattr(response, 'text'):
        return estimate_tokens(response.text)
    return 0
