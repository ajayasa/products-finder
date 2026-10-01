from __future__ import annotations

import re
from urllib.parse import quote_plus, urlparse


def clean_text(value) -> str:
    if value is None:
        return ''
    return re.sub(r'\s+', ' ', str(value)).strip()


def valid_product_url(url: str) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


def normalize_url(url: str) -> str:
    return clean_text(url).strip().rstrip('/')


def is_blocked_product(title: str, url: str, blocked_titles: set[str], blocked_urls: set[str]) -> bool:
    t = clean_text(title).lower()
    u = normalize_url(url).lower()
    if not t or not valid_product_url(u):
        return True
    if any(term in t for term in blocked_titles):
        return True
    if any(term in u for term in blocked_urls):
        return True
    return False


def make_search_links(name: str, marketplace_urls: dict[str, str]) -> dict[str, str]:
    q = quote_plus(clean_text(name))
    slug = re.sub(r'[^a-z0-9]+', '-', clean_text(name).lower()).strip('-')
    links = {}
    for marketplace, template in marketplace_urls.items():
        links[marketplace] = template.format(q=q, slug=slug)
    return links
