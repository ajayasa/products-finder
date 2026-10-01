from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

import requests

from .config import DEFAULT_LIANEX_URL, DEFAULT_LITTLE_BIRD_URL, DEFAULT_QUERY_PACK, TIMEOUT_SECONDS, USER_AGENT
from .normalize import clean_text, is_blocked_product, make_search_links, normalize_url
from .classify import classify
from .scoring import usefulness_score, uniqueness_score, opportunity_score, trend_label_from_evidence


@dataclass
class Product:
    product_id: str
    name: str
    source: str
    canonical_url: str
    image_url: str
    price: str
    currency: str
    availability: str
    brand: str
    description: str
    category: str
    seasons: list[str]
    trend_status: str
    trend_score: float | None
    usefulness_score: int
    uniqueness_score: int
    opportunity_score: int | None
    youtube_url: str
    instagram_url: str
    product_links: dict[str, str]
    direct_links: dict[str, str]
    verified: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SourceStatus:
    def __init__(self, name: str):
        self.name = name
        self.ok = False
        self.count = 0
        self.message = 'Not run'


class ProductCollector:
    def __init__(self, timeout: int = TIMEOUT_SECONDS):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT, 'Accept': 'application/json'})
        self.status: list[SourceStatus] = []

    def _get_json(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def collect_lianex(self, queries: list[str], per_query: int = 40) -> list[Product]:
        status = SourceStatus('Lianex')
        self.status.append(status)
        found: list[Product] = []
        try:
            for query in queries:
                payload = self._get_json(DEFAULT_LIANEX_URL, {
                    'q': query,
                    'limit': min(50, max(1, per_query)),
                    'compact': 'false',
                })
                rows = payload.get('products') or []
                for raw in rows:
                    p = self._from_lianex(raw)
                    if p:
                        found.append(p)
                if len(found) >= 500:
                    break
            status.ok = True
            status.count = len(found)
            status.message = f'Loaded {len(found)} records'
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
        return found

    def _from_lianex(self, raw: dict[str, Any]) -> Product | None:
        title = clean_text(raw.get('title') or raw.get('name'))
        url = normalize_url(raw.get('url') or raw.get('canonical_url') or raw.get('permalink'))
        if is_blocked_product(title, url, {
            'terms', 'privacy', 'cookie', 'sign in', 'login', 'contact us', 'help', 'about us',
            'account', 'checkout', 'cart', 'category', 'categories', 'search results'
        }, {
            '/terms', '/privacy', '/cookies', '/login', '/signin', '/sign-in', '/account', '/checkout', '/cart', '/help', '/contact', '/about', '/category/', '/categories/', '/search?'
        }):
            return None
        desc = clean_text(raw.get('description') or raw.get('summary'))
        category, seasons = classify(f'{title} {desc}')
        use = usefulness_score(title, desc)
        unique = uniqueness_score(title, desc)
        links = make_search_links(title, {
            'Amazon India': 'https://www.amazon.in/s?k={q}',
            'Flipkart': 'https://www.flipkart.com/search?q={q}',
            'Meesho': 'https://www.meesho.com/search?q={q}',
            'eBay': 'https://www.ebay.com/sch/i.html?_nkw={q}',
            'AliExpress': 'https://www.aliexpress.com/w/wholesale-{slug}.html',
            'Alibaba': 'https://www.alibaba.com/trade/search?SearchText={q}',
            'Etsy': 'https://www.etsy.com/search?q={q}',
            'Walmart': 'https://www.walmart.com/search?q={q}',
            'Target': 'https://www.target.com/s?searchTerm={q}',
            'Best Buy': 'https://www.bestbuy.com/site/searchpage.jsp?st={q}',
            'IndiaMART': 'https://dir.indiamart.com/search.mp?ss={q}',
        })
        direct = {'Source': url}
        marketplace = clean_text(raw.get('marketplace') or raw.get('provider') or 'Lianex')
        direct[marketplace] = url
        image = clean_text(raw.get('image') or raw.get('image_url') or raw.get('thumbnail'))
        pid = clean_text(raw.get('id') or raw.get('product_id') or raw.get('permalink') or url)
        price = raw.get('price')
        currency = clean_text(raw.get('currency'))
        return Product(
            product_id=pid,
            name=title,
            source=marketplace,
            canonical_url=url,
            image_url=image,
            price='' if price is None else str(price),
            currency=currency,
            availability=clean_text(raw.get('availability') or raw.get('condition')),
            brand=clean_text(raw.get('brand')),
            description=desc,
            category=category,
            seasons=seasons,
            trend_status='Unverified',
            trend_score=None,
            usefulness_score=use,
            uniqueness_score=unique,
            opportunity_score=opportunity_score(use, unique, None),
            youtube_url=f'https://www.youtube.com/results?search_query={__import__("urllib.parse").parse.quote_plus(title)}',
            instagram_url=f'https://www.instagram.com/explore/search/keyword/?q={__import__("urllib.parse").parse.quote_plus(title)}',
            product_links=links,
            direct_links=direct,
            verified=False,
        )

    def collect_little_bird(self, queries: list[str], per_query: int = 25, max_pages: int = 4) -> list[Product]:
        status = SourceStatus('Little Bird Electronics')
        self.status.append(status)
        found: list[Product] = []
        try:
            for query in queries:
                for page in range(1, max_pages + 1):
                    payload = self._get_json(DEFAULT_LITTLE_BIRD_URL, {
                        'q': query,
                        'page': page,
                        'per_page': min(100, max(1, per_query)),
                    })
                    rows = payload.get('products') or []
                    if not rows:
                        break
                    for raw in rows:
                        p = self._from_little_bird(raw)
                        if p:
                            found.append(p)
                    meta = payload.get('meta') or {}
                    total_pages = int(meta.get('total_pages') or page)
                    if page >= total_pages:
                        break
                if len(found) >= 250:
                    break
            status.ok = True
            status.count = len(found)
            status.message = f'Loaded {len(found)} records'
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
        return found

    def _from_little_bird(self, raw: dict[str, Any]) -> Product | None:
        title = clean_text(raw.get('title') or raw.get('name'))
        handle = clean_text(raw.get('handle'))
        url = clean_text(raw.get('url'))
        if not url and handle:
            url = f'https://littlebirdelectronics.com.au/products/{handle}'
        url = normalize_url(url)
        if is_blocked_product(title, url, {
            'terms', 'privacy', 'cookie', 'sign in', 'login', 'contact us', 'help', 'about us', 'account', 'checkout', 'cart', 'category', 'categories', 'search results'
        }, {'/terms', '/privacy', '/cookies', '/login', '/account', '/checkout', '/cart', '/help', '/contact', '/about', '/collections/', '/search?'}):
            return None
        desc = clean_text(raw.get('description') or raw.get('body_html'))
        category, seasons = classify(f'{title} {desc}')
        use = usefulness_score(title, desc)
        unique = uniqueness_score(title, desc)
        image = clean_text(raw.get('image') or raw.get('image_url'))
        if not image:
            images = raw.get('images') or []
            if images and isinstance(images[0], dict):
                image = clean_text(images[0].get('src') or images[0].get('url'))
            elif images and isinstance(images[0], str):
                image = images[0]
        price = raw.get('price')
        if price is None:
            variants = raw.get('variants') or []
            if variants and isinstance(variants[0], dict):
                price = variants[0].get('price')
        links = make_search_links(title, {
            'Amazon India': 'https://www.amazon.in/s?k={q}',
            'Flipkart': 'https://www.flipkart.com/search?q={q}',
            'Meesho': 'https://www.meesho.com/search?q={q}',
            'eBay': 'https://www.ebay.com/sch/i.html?_nkw={q}',
            'AliExpress': 'https://www.aliexpress.com/w/wholesale-{slug}.html',
            'Alibaba': 'https://www.alibaba.com/trade/search?SearchText={q}',
            'Etsy': 'https://www.etsy.com/search?q={q}',
            'Walmart': 'https://www.walmart.com/search?q={q}',
            'Target': 'https://www.target.com/s?searchTerm={q}',
            'Best Buy': 'https://www.bestbuy.com/site/searchpage.jsp?st={q}',
            'IndiaMART': 'https://dir.indiamart.com/search.mp?ss={q}',
        })
        links['Little Bird Electronics'] = url
        return Product(
            product_id=clean_text(raw.get('id') or handle or url),
            name=title,
            source='Little Bird Electronics',
            canonical_url=url,
            image_url=image,
            price='' if price is None else str(price),
            currency='AUD',
            availability='In stock' if raw.get('in_stock') else clean_text(raw.get('availability')),
            brand=clean_text(raw.get('vendor') or raw.get('brand')),
            description=desc,
            category=category,
            seasons=seasons,
            trend_status='Unverified',
            trend_score=None,
            usefulness_score=use,
            uniqueness_score=unique,
            opportunity_score=opportunity_score(use, unique, None),
            youtube_url=f'https://www.youtube.com/results?search_query={__import__("urllib.parse").parse.quote_plus(title)}',
            instagram_url=f'https://www.instagram.com/explore/search/keyword/?q={__import__("urllib.parse").parse.quote_plus(title)}',
            product_links=links,
            direct_links={'Little Bird Electronics': url},
            verified=False,
        )

    @staticmethod
    def exact_url_dedupe(products: list[Product]) -> list[Product]:
        seen: set[str] = set()
        out = []
        for p in products:
            key = normalize_url(p.canonical_url).lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out
