import requests
import fitz  # PyMuPDF
import io

def scrape_pdf(url):
    """Scrapes PDF content and converts to text using PyMuPDF."""
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        
        with fitz.open(stream=io.BytesIO(response.content), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()
            return text
    except Exception as e:
        print(f"PDF scraping error for {url}: {e}")
        return None
