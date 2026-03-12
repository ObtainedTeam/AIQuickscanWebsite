import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)
HEADERS = {"User-Agent": "Mozilla/5.0"}
TIMEOUT = 15

def scrape_website(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        html = resp.text
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script","style","noscript"]):
            tag.decompose()
        title = soup.find("title")
        title_text = title.get_text().strip() if title else ""
        headings = []
        for tag in ["h1","h2","h3"]:
            for el in soup.find_all(tag):
                text = el.get_text().strip()
                if text:
                    headings.append({"level": tag, "text": text})
        paragraphs = []
        for p in soup.find_all(["p","li"]):
            text = re.sub(r'\s+', ' ', p.get_text()).strip()
            if len(text) > 40:
                paragraphs.append(text)
        return {
            "url": url,
            "pages_scraped": 1,
            "homepage": {"title": title_text},
            "headings": headings[:30],
            "paragraphs": paragraphs[:30],
            "cta_texts": [],
            "forms": [],
            "tech_signals": [],
        }
    except Exception as e:
        raise ValueError(f"Could not scrape any content from {url}: {e}")
