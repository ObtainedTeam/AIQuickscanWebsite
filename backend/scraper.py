"""
scraper.py
Scrapes a B2B website and extracts meaningful content for AI analysis.
Uses requests + BeautifulSoup for clean text extraction.
"""

import re
import time
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "nl-NL,nl;q=0.9,en-US;q=0.8,en;q=0.7",
}
TIMEOUT = 15
MAX_PAGES = 6  # homepage + up to 5 internal pages


def clean_text(text: str) -> str:
    """Remove excessive whitespace and normalize."""
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def extract_page_data(url: str, html: str) -> dict:
    """Extract structured data from a single HTML page."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise
    for tag in soup(["script", "style", "noscript", "svg", "iframe", "nav", "footer", "header"]):
        tag.decompose()

    title = soup.find("title")
    title_text = clean_text(title.get_text()) if title else ""

    # Meta description
    meta_desc = ""
    for meta in soup.find_all("meta"):
        if meta.get("name", "").lower() == "description":
            meta_desc = meta.get("content", "")
            break

    # H1 / H2 / H3
    headings = []
    for tag in ["h1", "h2", "h3"]:
        for el in soup.find_all(tag):
            text = clean_text(el.get_text())
            if text and len(text) > 3:
                headings.append({"level": tag, "text": text})

    # Body paragraphs (meaningful content only)
    paragraphs = []
    for p in soup.find_all(["p", "li"]):
        text = clean_text(p.get_text())
        if len(text) > 40:  # skip short snippets
            paragraphs.append(text)
    paragraphs = paragraphs[:40]  # cap for token efficiency

    # CTA buttons / links text
    cta_texts = []
    for el in soup.find_all(["a", "button"]):
        text = clean_text(el.get_text())
        if 3 < len(text) < 60:
            cta_texts.append(text)
    cta_texts = list(dict.fromkeys(cta_texts))[:20]

    # Forms
    forms = []
    for form in soup.find_all("form"):
        inputs = [i.get("name", i.get("placeholder", "")) for i in form.find_all("input")]
        forms.append({"inputs": [x for x in inputs if x]})

    # Images with alt text
    images_with_alt = []
    for img in soup.find_all("img"):
        alt = img.get("alt", "").strip()
        if alt and len(alt) > 5:
            images_with_alt.append(alt)

    return {
        "url": url,
        "title": title_text,
        "meta_description": meta_desc,
        "headings": headings,
        "paragraphs": paragraphs,
        "cta_texts": cta_texts,
        "forms": forms,
        "images_alt": images_with_alt[:10],
    }


def get_internal_links(base_url: str, html: str) -> list[str]:
    """Extract internal links from a page, limited to same domain."""
    soup = BeautifulSoup(html, "html.parser")
    domain = urlparse(base_url).netloc
    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc == domain and parsed.scheme in ("http", "https"):
            # Skip anchors, files, and admin paths
            path = parsed.path.lower()
            if not any(path.endswith(ext) for ext in [".pdf", ".jpg", ".png", ".zip"]):
                if not any(seg in path for seg in ["/wp-admin", "/wp-login", "#", "?"]):
                    links.append(full_url.split("?")[0].split("#")[0])
    return list(dict.fromkeys(links))


def scrape_website(url: str) -> dict:
    """
    Scrape a website and return structured content for AI analysis.

    Returns a dict with:
        - homepage data
        - additional page data (up to MAX_PAGES total)
        - combined text summary
        - detected signals (forms, CTAs, tech stack hints)
    """
    if not url.startswith("http"):
        url = "https://" + url

    session = requests.Session()
    session.headers.update(HEADERS)

    pages_data = []
    visited = set()
    to_visit = [url]

    while to_visit and len(pages_data) < MAX_PAGES:
        current_url = to_visit.pop(0)
        if current_url in visited:
            continue
        visited.add(current_url)

        try:
            resp = session.get(current_url, timeout=TIMEOUT, allow_redirects=True)
            resp.raise_for_status()
            html = resp.text
            page_data = extract_page_data(current_url, html)
            pages_data.append(page_data)
            logger.info(f"Scraped: {current_url}")

            # Queue internal links (only from homepage)
            if len(pages_data) == 1:
                links = get_internal_links(url, html)
                # Prioritize important pages
                priority_keywords = ["diensten", "service", "over", "contact", "product",
                                     "oplossing", "work", "case", "blog", "about"]
                priority = [l for l in links if any(k in l.lower() for k in priority_keywords)]
                rest = [l for l in links if l not in priority]
                to_visit.extend(priority[:4] + rest[:2])

            time.sleep(0.5)  # polite crawling

        except Exception as e:
            logger.warning(f"Failed to scrape {current_url}: {e}")
            continue

    if not pages_data:
        raise ValueError(f"Could not scrape any content from {url}")

    # Build aggregated summary
    all_headings = []
    all_paragraphs = []
    all_ctas = []
    all_forms = []

    for page in pages_data:
        all_headings.extend(page["headings"])
        all_paragraphs.extend(page["paragraphs"])
        all_ctas.extend(page["cta_texts"])
        all_forms.extend(page["forms"])

    # Deduplicate
    seen_h = set()
    unique_headings = []
    for h in all_headings:
        if h["text"] not in seen_h:
            seen_h.add(h["text"])
            unique_headings.append(h)

    seen_p = set()
    unique_paragraphs = []
    for p in all_paragraphs:
        if p[:60] not in seen_p:
            seen_p.add(p[:60])
            unique_paragraphs.append(p)

    # Detect tech/platform signals from HTML
    homepage_html = ""
    try:
        resp = session.get(url, timeout=TIMEOUT)
        homepage_html = resp.text.lower()
    except:
        pass

    tech_signals = []
    tech_map = {
        "wordpress": "WordPress CMS",
        "woocommerce": "WooCommerce (e-commerce)",
        "shopify": "Shopify",
        "elementor": "Elementor page builder",
        "hubspot": "HubSpot CRM/Marketing",
        "salesforce": "Salesforce CRM",
        "zendesk": "Zendesk support",
        "intercom": "Intercom chat",
        "mailchimp": "Mailchimp email marketing",
        "google analytics": "Google Analytics",
        "hotjar": "Hotjar analytics",
        "livechat": "LiveChat",
        "tawk.to": "Tawk.to chat",
        "calendly": "Calendly scheduling",
        "typeform": "Typeform",
        "pipedrive": "Pipedrive CRM",
    }
    for key, label in tech_map.items():
        if key in homepage_html:
            tech_signals.append(label)

    return {
        "url": url,
        "pages_scraped": len(pages_data),
        "homepage": pages_data[0] if pages_data else {},
        "all_pages": pages_data,
        "headings": unique_headings[:50],
        "paragraphs": unique_paragraphs[:50],
        "cta_texts": list(dict.fromkeys(all_ctas))[:30],
        "forms": all_forms,
        "tech_signals": tech_signals,
    }
# force rebuild
