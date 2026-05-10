import requests
import fitz  # PyMuPDF
import io
from src.utils.user_agent import get_random_desktop_user_agent

def scrape_pdf(url):
    """Scrapes PDF content and converts to text using PyMuPDF."""
    try:
        session = requests.Session()
        user_agent = get_random_desktop_user_agent()
        session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'application/pdf,*/*',
            'Accept-Language': 'vi-VN,vi;q=0.9,en;q=0.8',
        })
        
        response = session.get(url, timeout=30)
        response.raise_for_status()
        
        with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        print(f"PDF scraping error for {url}: {e}")
        return None
