from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
from urllib.parse import quote_plus
import base64
import os
import uuid

import requests

from .config import (
    DEFAULT_LIANEX_URL,
    DEFAULT_LITTLE_BIRD_URL,
    DEFAULT_QUERY_PACK,
    TIMEOUT_SECONDS,
    USER_AGENT,
    LIANEX_MARKETPLACES,
    EBAY_TOKEN_URL,
    EBAY_BROWSE_URL,
    ETSY_LISTINGS_URL,
    WALMART_SEARCH_URL,
    MARKETPLACE_SEARCH_URLS,
    BLOCKED_TITLE_TERMS,
    BLOCKED_URL_TERMS,
    MAX_PRODUCTS,
)
from .normalize import clean_text, is_blocked_product, make_search_links, normalize_url
from .classify import classify
from .scoring import usefulness_score, uniqueness_score, opportunity_score


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
    """Collect real product listings from independent structured/public sources.

    The collector keeps similar listings separate. Only exact normalized URLs are
    removed after collection. Optional provider APIs are enabled only when their
    secrets are supplied through Streamlit secrets/environment variables.
    """

    def __init__(self, timeout: int = TIMEOUT_SECONDS, secrets: dict[str, Any] | None = None):
        self.timeout = timeout
        self.secrets = secrets or {}
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': USER_AGENT, 'Accept': 'application/json'})
        self.status: list[SourceStatus] = []

    def _get_json(self, url: str, params: dict[str, Any], headers: dict[str, str] | None = None) -> Any:
        response = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def _blocked(title: str, url: str) -> bool:
        return is_blocked_product(title, url, BLOCKED_TITLE_TERMS, BLOCKED_URL_TERMS)

    @staticmethod
    def _social_links(title: str) -> tuple[str, str]:
        q = quote_plus(title)
        return (
            f'https://www.youtube.com/results?search_query={q}',
            f'https://www.instagram.com/explore/search/keyword/?q={q}',
        )

    @staticmethod
    def _base_search_links(title: str) -> dict[str, str]:
        return make_search_links(title, MARKETPLACE_SEARCH_URLS)

    def _make_product(
        self,
        *,
        product_id: str,
        title: str,
        source: str,
        url: str,
        image: str = '',
        price: str = '',
        currency: str = '',
        availability: str = '',
        brand: str = '',
        description: str = '',
        direct_links: dict[str, str] | None = None,
        trend_status: str = 'Unverified',
        trend_score: float | None = None,
        verified: bool = False,
    ) -> Product | None:
        title = clean_text(title)
        url = normalize_url(url)
        if self._blocked(title, url):
            return None
        description = clean_text(description)
        category, seasons = classify(f'{title} {description}')
        use = usefulness_score(title, description)
        unique = uniqueness_score(title, description)
        youtube_url, instagram_url = self._social_links(title)
        links = self._base_search_links(title)
        exact = {k: normalize_url(v) for k, v in (direct_links or {}).items() if normalize_url(v)}
        # Always retain the actual source URL as an exact source link.
        exact.setdefault(source, url)
        return Product(
            product_id=clean_text(product_id) or url,
            name=title,
            source=source,
            canonical_url=url,
            image_url=clean_text(image),
            price=clean_text(price),
            currency=clean_text(currency),
            availability=clean_text(availability),
            brand=clean_text(brand),
            description=description,
            category=category,
            seasons=seasons,
            trend_status=trend_status,
            trend_score=trend_score,
            usefulness_score=use,
            uniqueness_score=unique,
            opportunity_score=opportunity_score(use, unique, trend_score),
            youtube_url=youtube_url,
            instagram_url=instagram_url,
            product_links=links,
            direct_links=exact,
            verified=verified,
        )

    # ---------- Lianex: no-key cached multi-marketplace catalogue ----------

    def collect_lianex(self, queries: list[str], per_query: int = 30) -> list[Product]:
        """Query Lianex independently for its currently documented marketplaces.

        Current Lianex search supports marketplace filters for ebay, amazon,
        aliexpress, jbhifi and shein. Querying them separately prevents an
        eBay-dominant unfiltered pool from crowding out other marketplaces.
        """
        found: list[Product] = []
        for marketplace_key, display_name in LIANEX_MARKETPLACES.items():
            status = SourceStatus(f'Lianex — {display_name}')
            self.status.append(status)
            try:
                count = 0
                for query in queries[:5]:
                    payload = self._get_json(DEFAULT_LIANEX_URL, {
                        'q': query,
                        'marketplace': marketplace_key,
                        'limit': min(50, max(1, per_query)),
                        'compact': 'false',
                        'dedupe': 'false',
                    })
                    if payload.get('result') not in (None, 'hit'):
                        # miss/not_searched are valid non-error states; do not label them as failures.
                        continue
                    for raw in payload.get('products') or []:
                        p = self._from_lianex(raw, display_name)
                        if p:
                            found.append(p)
                            count += 1
                status.ok = True
                status.count = count
                status.message = f'Loaded {count} records from {display_name} via Lianex cache'
            except Exception as exc:
                status.message = f'{type(exc).__name__}: {exc}'
        return found

    def _from_lianex(self, raw: dict[str, Any], forced_source: str) -> Product | None:
        title = clean_text(raw.get('title') or raw.get('name'))
        url = normalize_url(raw.get('url') or raw.get('canonical_url') or raw.get('permalink'))
        image = clean_text(raw.get('image') or raw.get('image_url') or raw.get('thumbnail'))
        pid = clean_text(raw.get('id') or raw.get('product_id') or raw.get('permalink') or url)
        price = raw.get('price')
        return self._make_product(
            product_id=pid,
            title=title,
            source=forced_source,
            url=url,
            image=image,
            price='' if price is None else str(price),
            currency=clean_text(raw.get('currency')),
            availability=clean_text(raw.get('availability') or raw.get('condition')),
            brand=clean_text(raw.get('brand')),
            description=clean_text(raw.get('description') or raw.get('summary')),
            direct_links={forced_source: url},
            verified=False,
        )

    # ---------- Little Bird Electronics: no-key public JSON catalogue ----------

    def collect_little_bird(self, queries: list[str], per_query: int = 25, max_pages: int = 4) -> list[Product]:
        status = SourceStatus('Little Bird Electronics')
        self.status.append(status)
        found: list[Product] = []
        try:
            for query in queries[:6]:
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
            status.ok = True
            status.count = len(found)
            status.message = f'Loaded {len(found)} electronics records'
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
        return found

    def _from_little_bird(self, raw: dict[str, Any]) -> Product | None:
        title = clean_text(raw.get('title') or raw.get('name'))
        handle = clean_text(raw.get('handle'))
        url = clean_text(raw.get('url')) or (f'https://littlebirdelectronics.com.au/products/{handle}' if handle else '')
        image = clean_text(raw.get('image') or raw.get('image_url'))
        if not image:
            images = raw.get('images') or []
            if images and isinstance(images[0], dict):
                image = clean_text(images[0].get('src') or images[0].get('url'))
            elif images and isinstance(images[0], str):
                image = clean_text(images[0])
        price = raw.get('price')
        if price is None:
            variants = raw.get('variants') or []
            if variants and isinstance(variants[0], dict):
                price = variants[0].get('price')
        return self._make_product(
            product_id=clean_text(raw.get('id') or handle or url),
            title=title,
            source='Little Bird Electronics',
            url=url,
            image=image,
            price='' if price is None else str(price),
            currency=clean_text(raw.get('currency') or 'AUD'),
            availability='In stock' if raw.get('in_stock') else clean_text(raw.get('availability')),
            brand=clean_text(raw.get('vendor') or raw.get('brand')),
            description=clean_text(raw.get('description') or raw.get('body_html')),
            direct_links={'Little Bird Electronics': url},
            verified=False,
        )

    # ---------- Optional official provider APIs ----------

    def collect_ebay_official(self, queries: list[str], marketplace_id: str = 'EBAY_US', max_items: int = 40) -> list[Product]:
        status = SourceStatus('eBay official Browse API')
        self.status.append(status)
        client_id = self.secrets.get('EBAY_CLIENT_ID') or os.getenv('EBAY_CLIENT_ID', '')
        client_secret = self.secrets.get('EBAY_CLIENT_SECRET') or os.getenv('EBAY_CLIENT_SECRET', '')
        if not client_id or not client_secret:
            status.message = 'Skipped — EBAY_CLIENT_ID/EBAY_CLIENT_SECRET not configured; Lianex eBay source remains available.'
            return []
        try:
            basic = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
            token_resp = self.session.post(
                EBAY_TOKEN_URL,
                headers={
                    'Authorization': f'Basic {basic}',
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                data={'grant_type': 'client_credentials', 'scope': 'https://api.ebay.com/oauth/api_scope'},
                timeout=self.timeout,
            )
            token_resp.raise_for_status()
            token = token_resp.json()['access_token']
            count = 0
            out: list[Product] = []
            for query in queries[:5]:
                data = self._get_json(
                    EBAY_BROWSE_URL,
                    {'q': query, 'limit': min(50, max_items)},
                    headers={'Authorization': f'Bearer {token}', 'X-EBAY-C-MARKETPLACE-ID': marketplace_id},
                )
                for item in data.get('itemSummaries') or []:
                    p = self._make_product(
                        product_id=str(item.get('itemId') or item.get('legacyItemId') or item.get('itemWebUrl') or uuid.uuid4()),
                        title=item.get('title') or '',
                        source='eBay',
                        url=item.get('itemWebUrl') or '',
                        image=((item.get('image') or {}).get('imageUrl') if isinstance(item.get('image'), dict) else ''),
                        price=str((item.get('price') or {}).get('value') or ''),
                        currency=str((item.get('price') or {}).get('currency') or ''),
                        availability='Available',
                        brand=str(item.get('brand') or ''),
                        description='',
                        direct_links={'eBay': item.get('itemWebUrl') or ''},
                        verified=True,
                    )
                    if p:
                        out.append(p)
                        count += 1
            status.ok = True
            status.count = count
            status.message = f'Loaded {count} listings from eBay Browse API'
            return out
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
            return []

    def collect_etsy_official(self, queries: list[str], max_items: int = 40) -> list[Product]:
        status = SourceStatus('Etsy official Open API')
        self.status.append(status)
        api_key = self.secrets.get('ETSY_API_KEY') or os.getenv('ETSY_API_KEY', '')
        if not api_key:
            status.message = 'Skipped — ETSY_API_KEY not configured.'
            return []
        found: list[Product] = []
        try:
            for query in queries[:4]:
                data = self._get_json(
                    ETSY_LISTINGS_URL,
                    {'keywords': query, 'limit': min(100, max_items), 'state': 'active'},
                    headers={'x-api-key': api_key},
                )
                # Different Etsy deployments may require OAuth; failures are isolated and shown in status.
                for item in data.get('results') or []:
                    p = self._make_product(
                        product_id=str(item.get('listing_id') or item.get('url') or uuid.uuid4()),
                        title=item.get('title') or '',
                        source='Etsy',
                        url=item.get('url') or '',
                        image=(item.get('images')[0].get('url_570xN') if item.get('images') and isinstance(item['images'][0], dict) else ''),
                        price=str(((item.get('price') or {}).get('amount') or '')),
                        currency=str(((item.get('price') or {}).get('currency_code') or '')),
                        availability='Active',
                        description=item.get('description') or '',
                        direct_links={'Etsy': item.get('url') or ''},
                        verified=True,
                    )
                    if p:
                        found.append(p)
            status.ok = True
            status.count = len(found)
            status.message = f'Loaded {len(found)} listings from Etsy API'
            return found
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
            return []

    def collect_walmart_official(self, queries: list[str], market: str = 'us', max_items: int = 40) -> list[Product]:
        status = SourceStatus(f'Walmart official API ({market.upper()})')
        self.status.append(status)
        token = self.secrets.get('WALMART_ACCESS_TOKEN') or os.getenv('WALMART_ACCESS_TOKEN', '')
        if not token:
            status.message = 'Skipped — WALMART_ACCESS_TOKEN not configured.'
            return []
        found: list[Product] = []
        try:
            for query in queries[:4]:
                headers = {
                    'WM_SEC.ACCESS_TOKEN': token,
                    'WM_QOS.CORRELATION_ID': str(uuid.uuid4()),
                    'WM_SVC.NAME': 'Product Hunter',
                    'WM_GLOBAL_VERSION': '3.1',
                    'WM_MARKET': market,
                    'Accept': 'application/json',
                }
                data = self._get_json(WALMART_SEARCH_URL, {'query': query}, headers=headers)
                for item in data.get('items') or []:
                    img = ''
                    images = item.get('images') or []
                    if images and isinstance(images[0], dict):
                        img = images[0].get('url') or images[0].get('imageUrl') or ''
                    p = self._make_product(
                        product_id=str(item.get('itemId') or item.get('productId') or item.get('sku') or uuid.uuid4()),
                        title=item.get('title') or item.get('itemName') or '',
                        source='Walmart',
                        url=item.get('productPageUrl') or item.get('productUrl') or item.get('canonicalUrl') or '',
                        image=img,
                        price=str(item.get('price') or ''),
                        currency=str(item.get('currency') or 'USD'),
                        availability='Published',
                        brand=str(item.get('brand') or ''),
                        description=item.get('description') or '',
                        direct_links={'Walmart': item.get('productPageUrl') or item.get('productUrl') or item.get('canonicalUrl') or ''},
                        verified=True,
                    )
                    if p:
                        found.append(p)
            status.ok = True
            status.count = len(found)
            status.message = f'Loaded {len(found)} listings from Walmart API'
            return found
        except Exception as exc:
            status.message = f'{type(exc).__name__}: {exc}'
            return []

    def collect_all(self, query: str = '') -> list[Product]:
        queries = [query] if query.strip() else DEFAULT_QUERY_PACK
        products: list[Product] = []
        # No single source is allowed to stop the run.
        products.extend(self.collect_lianex(queries, per_query=30))
        products.extend(self.collect_little_bird(queries, per_query=25, max_pages=3))
        products.extend(self.collect_ebay_official(queries))
        products.extend(self.collect_etsy_official(queries))
        products.extend(self.collect_walmart_official(queries))
        return self.exact_url_dedupe(products)[:MAX_PRODUCTS]

    @staticmethod
    def exact_url_dedupe(products: list[Product]) -> list[Product]:
        seen: set[str] = set()
        out: list[Product] = []
        for p in products:
            key = normalize_url(p.canonical_url).lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(p)
        return out
