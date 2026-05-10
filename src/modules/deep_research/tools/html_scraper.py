import trafilatura

def scrape_html(url):
    """Scrapes HTML content and converts to text using trafilatura."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if downloaded is None:
            return None
        return trafilatura.extract(downloaded)
    except Exception as e:
        print(f"HTML scraping error for {url}: {e}")
        return None
