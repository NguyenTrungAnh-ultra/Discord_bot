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
    from src.config.config_loader import Config

    provider = Config.get("llm", "provider", "gemini")
    ollama_url = Config.get("llm", "ollama_url", "http://localhost:11434")

    if client is None and provider == "gemini":
        client = get_genai_client()

    current_input_tokens = state.get("total_input_tokens", 0)
    current_output_tokens = state.get("total_output_tokens", 0)
    current_requests = state.get("total_requests", 0)
    node_tokens = state.get("node_tokens", {})
    
    node_input = estimate_tokens(prompt)
    current_requests += 1
    current_input_tokens += node_input

    config = None
    if json_mode and provider == "gemini":
        config = types.GenerateContentConfig(response_mime_type="application/json")

    from tenacity import retry, stop_after_attempt, wait_exponential

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _generate():
        if provider == "ollama":
            import requests
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
            if json_mode:
                payload["format"] = "json"
                
            response = requests.post(f"{ollama_url}/api/chat", json=payload, timeout=120)
            response.raise_for_status()
            res_json = response.json()
            
            # Create a mock response object matching the interface expected below
            class OllamaResponse:
                def __init__(self, text, output_tokens):
                    self.text = text
                    self.usage_metadata = type('Usage', (), {'candidates_token_count': output_tokens})()
            
            output_tokens = res_json.get("eval_count", estimate_tokens(res_json["message"]["content"]))
            return OllamaResponse(res_json["message"]["content"], output_tokens)
        else:
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
