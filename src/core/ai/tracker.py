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

def call_llm_with_tracking(state: dict, node_name: str, prompt: str, model_name: str, json_mode: bool = False, client=None):
    """
    Calls the LLM, tracks input/output tokens, and updates state counters.
    Returns (response_text, updated_state_dict) or raises Exception.
    """
    import os
    from google import genai
    from google.genai import types
    from src.core.ai.client import get_genai_client

    if client is None:
        client = get_genai_client()

    current_input_tokens = state.get("total_input_tokens", 0)
    current_output_tokens = state.get("total_output_tokens", 0)
    current_requests = state.get("total_requests", 0)
    node_tokens = state.get("node_tokens", {})
    
    node_input = estimate_tokens(prompt)
    current_requests += 1
    current_input_tokens += node_input

    config = None
    if json_mode:
        config = types.GenerateContentConfig(response_mime_type="application/json")

    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate():
        return client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

    try:
        response = _generate()
        node_output = count_response_tokens(response)
        current_output_tokens += node_output
        
        node_entry = node_tokens.get(node_name, {"input": 0, "output": 0})
        node_tokens[node_name] = {
            "input": node_entry["input"] + node_input,
            "output": node_entry["output"] + node_output
        }
        
        updated_state = {
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
        
        return response.text, updated_state
    except Exception as e:
        # Update tokens even on failure if we want to track input
        node_entry = node_tokens.get(node_name, {"input": 0, "output": 0})
        node_tokens[node_name] = {
            "input": node_entry["input"] + node_input,
            "output": node_entry["output"]
        }
        updated_state = {
            "total_input_tokens": current_input_tokens,
            "total_output_tokens": current_output_tokens,
            "total_requests": current_requests,
            "node_tokens": node_tokens
        }
        print(f"LLM Error after retries in {node_name}: {str(e)}")
        # Fallback to prevent crash
        return '{"error": "AI unavailable"}', updated_state
