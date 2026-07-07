import requests
import fitz  # PyMuPDF
import io
import concurrent.futures
from src.core.scraper.browser import get_random_desktop_user_agent
from src.core.scraper.security import is_safe_url

def _do_scrape_pdf(url):
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

def scrape_pdf(url):
    """Scrapes PDF content and converts to text using PyMuPDF."""
    if not is_safe_url(url):
        print(f"SSRF blocked for URL: {url}")
        return None

    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_do_scrape_pdf, url)
            # Global timeout of 30 seconds
            return future.result(timeout=30)
    except concurrent.futures.TimeoutError:
        print(f"Global timeout exceeded (30s) while scraping PDF: {url}")
        return None
    except Exception as e:
        print(f"PDF scraping error for {url}: {e}")
        return None
