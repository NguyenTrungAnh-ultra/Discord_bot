import os
from google import genai
from dotenv import load_dotenv

_client = None

def get_genai_client():
    global _client
    if _client is None:
        load_dotenv()
        _client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    return _client
