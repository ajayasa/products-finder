from __future__ import annotations

import html
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

import pandas as pd
import requests
import streamlit as st

APP_VERSION = "Product Hunter v27 — Structured Data Build"
PAGE_SIZE = 100
TOTAL_PAGES = 5
MAX_PRODUCTS = PAGE_SIZE * TOTAL_PAGES
REQUEST_TIMEOUT = (3, 9)
LIANEX_BASE = "https://api.lianex.ai"
LITTLE_BIRD_BASE = "https://littlebirdelectronics.com.au"

CATEGORIES = [
    "Unique & Clever", "Problem-Solving", "Home & Kitchen", "Tech & Gadgets",
    "Car & Bike", "Travel", "Personal Use & Grooming", "Village / Rural",
    "Farming & Agriculture", "Seasonal", "Outdoor & Garden", "Tools & DIY",
    "Cleaning & Organization", "Safety & Emergency", "Kids & Parents",
    "Elderly / Senior-Friendly", "Office & Work From Home", "Money-Saving",
    "Local / Indian-Specific",
]
SEASONS = [
    "Summer", "Monsoon", "Winter", "Sankranti", "Ugadi", "Dasara / Dussehra",
    "Diwali", "Christmas / New Year", "Wedding season", "School / college reopening",
    "Travel season", "Festival-specific",
]
TARGET_MARKETPLACES = [
    "Amazon", "eBay", "AliExpress", "JB Hi-Fi", "Shein", "Flipkart", "Meesho",
    "Alibaba", "Etsy", "Walmart", "Target", "Best Buy", "Ubuy", "IndiaMART",
    "Temu", "Shopee", "Lazada",
]

DISCOVERY_QUERIES = [
    "unique useful gadgets", "problem solving products", "home kitchen gadgets",
    "smart home useful products", "car bike accessories", "travel gadgets",
    "personal grooming gadgets", "outdoor garden tools", "tools DIY products",
    "cleaning organization gadgets", "safety emergency products", "kids useful products",
    "elderly senior friendly products", "office work from home gadgets", "money saving products",
    "rural village useful products", "farming agriculture tools", "summer useful products",
    "monsoon rain products", "winter useful products", "festival products", "small space storage",
]
MARKETPLACE_QUERIES = [
    ("amazon", "useful gadgets"), ("ebay", "unique products"), ("aliexpress", "smart gadgets"),
    ("jbhifi", "electronics accessories"), ("shein", "useful daily products"),
    ("amazon", "kitchen gadgets"), ("ebay", "car accessories"), ("aliexpress", "travel gadgets"),
]
LITTLE_BIRD_QUERIES = ["gadgets", "electronics", "tools", "arduino", "sensors", "smart home"]

BLOCKED_TITLE_TERMS = {
    "terms of use", "terms", "privacy policy", "cookie policy", "cookies",
    "do not sell my personal information", "sign in", "sign up", "login", "log in",
    "account", "help", "help center", "contact", "about us", "about", "careers",
    "shipping", "returns", "refund policy", "accessibility", "sitemap", "store locator",
    "track order", "customer service", "seller center", "affiliate", "press", "blog",
    "home", "search results", "category", "categories", "collection", "collections",
}
BLOCKED_URL_PARTS = (
    "/terms", "/privacy", "/cookie", "/account", "/login", "/signin", "/signup",
    "/help", "/contact", "/about", "/careers", "/support", "/returns", "/refund",
    "/shipping", "/sitemap", "/search", "?q=", "?query=", "/category/", "/categories/",
    "/collections/", "/seller", "/affiliate", "/press", "/blog",
)

CATEGORY_RULES = [
    ("Tech & Gadgets", ["gadget", "usb", "bluetooth", "charger", "power bank", "smart", "led", "sensor", "camera", "electronic"]),
    ("Home & Kitchen", ["kitchen", "cooking", "storage", "organizer", "home", "sink", "drawer", "spice", "bottle", "rack"]),
    ("Car & Bike", ["car", "bike", "motorcycle", "automotive", "tyre", "tire", "dashboard", "vehicle"]),
    ("Travel", ["travel", "luggage", "suitcase", "passport", "camping", "portable"]),
    ("Personal Use & Grooming", ["grooming", "shaver", "hair", "beauty", "skin", "personal care", "toothbrush"]),
    ("Tools & DIY", ["tool", "drill", "screwdriver", "wrench", "diy", "workshop", "repair"]),
    ("Outdoor & Garden", ["garden", "outdoor", "watering", "plant", "camp", "patio"]),
    ("Cleaning & Organization", ["cleaning", "organizer", "organise", "storage", "vacuum", "mop", "brush"]),
    ("Kids & Parents", ["kid", "baby", "child", "parent", "toy", "feeding"]),
    ("Office & Work From Home", ["office", "desk", "laptop", "keyboard", "mouse", "workspace", "monitor"]),
    ("Safety & Emergency", ["safety", "emergency", "first aid", "alarm", "security", "reflective"]),
    ("Farming & Agriculture", ["farm", "farming", "agriculture", "irrigation", "seed", "crop", "sprayer"]),
    ("Village / Rural", ["rural", "village", "well", "water pump", "livestock", "barn"]),
    ("Elderly / Senior-Friendly", ["senior", "elderly", "mobility", "assist", "arthritis"]),
    ("Money-Saving", ["saving", "reusable", "energy saving", "economy", "budget"]),
    ("Problem-Solving", ["problem", "solution", "anti-slip", "space saving", "leak", "clog", "odor"]),
    ("Seasonal", ["summer", "monsoon", "rain", "winter", "festival", "diwali", "christmas", "sankranti", "ugadi"]),
]

SEASON_RULES = {
    "Summer": ["summer", "cooling", "heat", "sun", "ice", "hydration"],
    "Monsoon": ["monsoon", "rain", "waterproof", "umbrella", "drain", "mold", "moisture"],
    "Winter": ["winter", "warm", "heater", "thermal", "cold", "fleece"],
    "Sankranti": ["sankranti", "pongal", "kolam", "rangoli"],
    "Ugadi": ["ugadi", "ugadi festival"],
    "Dasara / Dussehra": ["dussehra", "dasara", "navaratri"],
    "Diwali": ["diwali", "deepavali", "deepawali"],
    "Christmas / New Year": ["christmas", "new year", "xmas"],
    "Wedding season": ["wedding", "bridal", "marriage"],
    "School / college reopening": ["school", "college", "student", "back to school"],
    "Travel season": ["travel", "holiday", "vacation", "camping"],
    "Festival-specific": ["festival", "puja", "pooja", "decor", "decoration"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_url(url: Any) -> str:
    if not url:
        return ""
    u = safe_text(url)
    if not u.lower().startswith(("http://", "https://")):
        return ""
    try:
        p = urlparse(u)
        return f"{p.scheme.lower()}://{p.netloc.lower()}{p.path.rstrip('/')}{('?' + p.query) if p.query else ''}"
    except Exception:
        return u


def is_valid_http_url(url: Any) -> bool:
    n = normalize_url(url)
    if not n:
        return False
    try:
        p = urlparse(n)
        return p.scheme in {"http", "https"} and bool(p.netloc)
    except Exception:
        return False


def is_blocked_product_page(title: Any, url: Any) -> bool:
    t = safe_text(title).lower()
    u = normalize_url(url).lower()
    if not t or not u:
        return True
    if any(x in t for x in BLOCKED_TITLE_TERMS):
        return True
    if any(part in u for part in BLOCKED_URL_PARTS):
        return True
    # Strong reject for obvious navigation-only URL paths.
    path = urlparse(u).path.lower()
    if path in {"/", "/home", "/index", "/search", "/help", "/contact", "/about"}:
        return True
    return False


def source_label(provider: Any, marketplace: Any = None, url: Any = None) -> str:
    raw = safe_text(marketplace or provider).lower()
    mapping = {
        "amazon": "Amazon", "ebay": "eBay", "aliexpress": "AliExpress",
        "jbhifi": "JB Hi-Fi", "shein": "Shein", "flipkart": "Flipkart",
        "meesho": "Meesho", "littlebird": "Little Bird Electronics",
    }
    if raw in mapping:
        return mapping[raw]
    host = urlparse(normalize_url(url)).netloc.lower()
    if "amazon" in host: return "Amazon"
    if "ebay" in host: return "eBay"
    if "aliexpress" in host: return "AliExpress"
    if "littlebirdelectronics" in host: return "Little Bird Electronics"
    return safe_text(provider) or "Unknown"


def classify_category(title: str, description: str, source: str) -> str:
    text = f"{title} {description} {source}".lower()
    for category, terms in CATEGORY_RULES:
        if any(term in text for term in terms):
            return category
    return "Unique & Clever"


def classify_seasons(title: str, description: str) -> List[str]:
    text = f"{title} {description}".lower()
    result = []
    for season, terms in SEASON_RULES.items():
        if any(term in text for term in terms):
            result.append(season)
    return result or ["All-Year"]


def heuristic_scores(title: str, description: str) -> Tuple[int, int, int]:
    text = f"{title} {description}".lower()
    usefulness_terms = ["useful", "solution", "organizer", "storage", "save", "safety", "portable", "clean", "protect", "repair", "smart"]
    uniqueness_terms = ["unique", "clever", "innovative", "multifunction", "foldable", "compact", "novel", "2 in 1", "3 in 1"]
    problem_terms = ["problem", "anti", "leak", "space saving", "odor", "spill", "dust", "rain", "heat", "clutter"]
    usefulness = min(99, 55 + 4 * sum(x in text for x in usefulness_terms))
    uniqueness = min(99, 55 + 5 * sum(x in text for x in uniqueness_terms))
    opportunity = min(99, int((usefulness * 0.45) + (uniqueness * 0.35) + min(20, 5 * sum(x in text for x in problem_terms))))
    return usefulness, uniqueness, opportunity


def marketplace_search_links(title: str) -> List[Tuple[str, str, str]]:
    q = quote_plus(title)
    links = []
    templates = [
        ("Amazon", f"https://www.amazon.com/s?k={q}"),
        ("Amazon India", f"https://www.amazon.in/s?k={q}"),
        ("eBay", f"https://www.ebay.com/sch/i.html?_nkw={q}"),
        ("AliExpress", f"https://www.aliexpress.com/w/wholesale-{quote_plus(title)}.html"),
        ("Flipkart", f"https://www.flipkart.com/search?q={q}"),
        ("Meesho", f"https://www.meesho.com/search?q={q}"),
        ("Etsy", f"https://www.etsy.com/search?q={q}"),
        ("Walmart", f"https://www.walmart.com/search?q={q}"),
        ("Target", f"https://www.target.com/s?searchTerm={q}"),
        ("Best Buy", f"https://www.bestbuy.com/site/searchpage.jsp?st={q}"),
        ("Ubuy", f"https://www.ubuy.com/en/search/?q={q}"),
        ("IndiaMART", f"https://dir.indiamart.com/search.mp?ss={q}"),
        ("Temu", f"https://www.temu.com/search_result.html?search_key={q}"),
        ("Shopee", f"https://shopee.com/search?keyword={q}"),
        ("Lazada", f"https://www.lazada.com/catalog/?q={q}"),
    ]
    for name, url in templates:
        links.append((name, url, "search"))
    return links


def normalize_lianex_product(raw: Dict[str, Any], query: str = "") -> Optional[Dict[str, Any]]:
    title = safe_text(raw.get("title"))
    url = normalize_url(raw.get("url"))
    image = normalize_url(raw.get("image"))
    if not title or not url or is_blocked_product_page(title, url):
        return None
    provider = safe_text(raw.get("provider")) or source_label(None, None, url)
    marketplace = safe_text(raw.get("marketplace"))
    source = source_label(provider, marketplace, url)
    description = safe_text(raw.get("description") or raw.get("reason") or "")
    category = classify_category(title, description, source)
    seasons = classify_seasons(title, description)
    usefulness, uniqueness, opportunity = heuristic_scores(title, description)
    price = safe_text(raw.get("price") or raw.get("from_price"))
    currency = safe_text(raw.get("currency"))
    availability = safe_text(raw.get("availability") or raw.get("condition"))
    product_id = safe_text(raw.get("id") or raw.get("item_id")) or url
    return {
        "product_id": product_id,
        "title": title,
        "canonical_url": url,
        "source": source,
        "image_url": image,
        "price": price,
        "currency": currency,
        "availability": availability,
        "brand": safe_text(raw.get("brand")),
        "description": description,
        "category": category,
        "season": ", ".join(seasons),
        "trend_status": "Unverified",
        "trend_score": None,
        "usefulness_score": usefulness,
        "uniqueness_score": uniqueness,
        "opportunity_score": opportunity,
        "youtube_reference_url": f"https://www.youtube.com/results?search_query={quote_plus(title)}",
        "instagram_reference_url": f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(title)}",
        "created_at": utc_now(),
        "last_checked_at": utc_now(),
        "query": query,
        "marketplace": provider,
        "aggregator": "Lianex public API",
        "product_links": marketplace_search_links(title),
    }


def normalize_little_bird_product(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title = safe_text(raw.get("title") or raw.get("name"))
    handle = safe_text(raw.get("handle"))
    url = normalize_url(raw.get("url"))
    if not url and handle:
        url = f"{LITTLE_BIRD_BASE}/products/{quote(handle, safe="")}"
    if not title or not url or is_blocked_product_page(title, url):
        return None
    images = raw.get("images") or raw.get("image") or []
    if isinstance(images, str):
        image = normalize_url(images)
    elif isinstance(images, list) and images:
        first = images[0]
        image = normalize_url(first.get("src") if isinstance(first, dict) else first)
    else:
        image = ""
    description = safe_text(raw.get("description") or raw.get("body_html") or "")
    price = safe_text(raw.get("price"))
    currency = safe_text(raw.get("currency") or "AUD")
    category = classify_category(title, description, "Little Bird Electronics")
    seasons = classify_seasons(title, description)
    usefulness, uniqueness, opportunity = heuristic_scores(title, description)
    product_id = safe_text(raw.get("id") or raw.get("sku") or handle or url)
    return {
        "product_id": product_id,
        "title": title,
        "canonical_url": url,
        "source": "Little Bird Electronics",
        "image_url": image,
        "price": price,
        "currency": currency,
        "availability": safe_text(raw.get("availability") or raw.get("inventory_quantity") or ""),
        "brand": safe_text(raw.get("vendor") or raw.get("brand")),
        "description": description,
        "category": category,
        "season": ", ".join(seasons),
        "trend_status": "Unverified",
        "trend_score": None,
        "usefulness_score": usefulness,
        "uniqueness_score": uniqueness,
        "opportunity_score": opportunity,
        "youtube_reference_url": f"https://www.youtube.com/results?search_query={quote_plus(title)}",
        "instagram_reference_url": f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(title)}",
        "created_at": utc_now(),
        "last_checked_at": utc_now(),
        "query": "Little Bird",
        "marketplace": "littlebird",
        "aggregator": "Little Bird public API",
        "product_links": marketplace_search_links(title),
    }


def get_json(url: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Tuple[Optional[Dict[str, Any]], str]:
    try:
        h = {
            "User-Agent": "ProductHunter/27 (+https://streamlit.io)",
            "Accept": "application/json",
        }
        if headers:
            h.update(headers)
        response = requests.get(url, params=params, headers=h, timeout=REQUEST_TIMEOUT)
        status = response.status_code
        if status == 429:
            retry_after = safe_text(response.headers.get("Retry-After"))
            return None, f"HTTP 429 rate-limited (Retry-After {retry_after or 'unknown'}s)"
        if status >= 400:
            return None, f"HTTP {status}"
        data = response.json()
        if not isinstance(data, dict):
            return None, "Invalid JSON object"
        return data, "ok"
    except requests.Timeout:
        return None, "timeout"
    except requests.RequestException as exc:
        return None, f"network error: {type(exc).__name__}"
    except ValueError:
        return None, "invalid JSON"
    except Exception as exc:
        return None, f"unexpected error: {type(exc).__name__}"


def fetch_lianex_query(query: str, marketplace: Optional[str] = None) -> Tuple[List[Dict[str, Any]], str]:
    params: Dict[str, Any] = {"q": query, "limit": 50}
    if marketplace:
        params["marketplace"] = marketplace
    data, status = get_json(f"{LIANEX_BASE}/api/public/search", params=params)
    if data is None:
        return [], status
    if data.get("result") != "hit":
        return [], safe_text(data.get("message") or data.get("result") or "no matches")
    products = data.get("products") or []
    rows: List[Dict[str, Any]] = []
    for raw in products:
        if isinstance(raw, dict):
            item = normalize_lianex_product(raw, query=query)
            if item:
                rows.append(item)
    return rows, f"ok ({len(rows)})"


def fetch_little_bird_query(query: str) -> Tuple[List[Dict[str, Any]], str]:
    params = {"q": query, "page": 1, "per_page": 100}
    data, status = get_json(f"{LITTLE_BIRD_BASE}/public-api/v1/products", params=params)
    if data is None:
        return [], status
    raw_products = data.get("products") or []
    rows = []
    for raw in raw_products:
        if isinstance(raw, dict):
            item = normalize_little_bird_product(raw)
            if item:
                rows.append(item)
    return rows, f"ok ({len(rows)})"


def exact_url_dedupe(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for record in records:
        url = normalize_url(record.get("canonical_url"))
        if not url or url in seen:
            continue
        seen.add(url)
        out.append(record)
    return out


def diversify(records: List[Dict[str, Any]], target: int = MAX_PRODUCTS) -> List[Dict[str, Any]]:
    """Keep similar products separate but prevent one marketplace from dominating when alternatives exist."""
    if not records:
        return []
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        grouped.setdefault(r["source"], []).append(r)
    source_count = max(1, len(grouped))
    cap = max(40, int(target / max(2, min(source_count, 5))))
    output: List[Dict[str, Any]] = []
    # Round robin by source first.
    exhausted = False
    idx = 0
    while len(output) < target and not exhausted:
        exhausted = True
        for source, rows in grouped.items():
            if idx < len(rows) and sum(x["source"] == source for x in output) < cap:
                output.append(rows[idx])
                exhausted = False
                if len(output) >= target:
                    break
        idx += 1
    # Fill remainder without changing relative/listing separation.
    if len(output) < target:
        used = {x["canonical_url"] for x in output}
        for r in records:
            if r["canonical_url"] not in used:
                output.append(r)
                if len(output) >= target:
                    break
    return output[:target]


def build_health(rows: List[Tuple[str, str, int]], started: float) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["source", "status", "records"]).assign(seconds=lambda d: round(time.perf_counter() - started, 2))


def collect_global_products(target: int = MAX_PRODUCTS) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    started = time.perf_counter()
    all_rows: List[Dict[str, Any]] = []
    health: List[Tuple[str, str, int]] = []
    tasks: List[Tuple[str, Optional[str]]] = [(q, None) for q in DISCOVERY_QUERIES[:16]]
    tasks.extend(MARKETPLACE_QUERIES)
    with ThreadPoolExecutor(max_workers=10) as pool:
        future_map = {pool.submit(fetch_lianex_query, q, marketplace): (q, marketplace) for q, marketplace in tasks}
        for future in as_completed(future_map):
            q, marketplace = future_map[future]
            label = f"Lianex/{marketplace or 'general'}: {q}"
            try:
                rows, status = future.result()
            except Exception as exc:
                rows, status = [], f"collector error: {type(exc).__name__}"
            all_rows.extend(rows)
            health.append((label, status, len(rows)))

    all_rows = exact_url_dedupe(all_rows)

    # Backup structured public API when the primary source is unavailable or thin.
    if len(all_rows) < min(400, target):
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(fetch_little_bird_query, q): q for q in LITTLE_BIRD_QUERIES}
            for future in as_completed(futures):
                q = futures[future]
                try:
                    rows, status = future.result()
                except Exception as exc:
                    rows, status = [], f"collector error: {type(exc).__name__}"
                all_rows.extend(rows)
                health.append((f"Little Bird: {q}", status, len(rows)))
        all_rows = exact_url_dedupe(all_rows)

    diversified = diversify(all_rows, target=target)
    return diversified, build_health(health, started)


@st.cache_data(ttl=900, show_spinner=False)
def cached_global_products() -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    rows, health = collect_global_products(MAX_PRODUCTS)
    return rows, health.to_dict("records")


def local_search(records: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    q = safe_text(query).lower()
    if not q:
        return records
    words = [w for w in re.findall(r"[a-z0-9]+", q) if len(w) > 1]
    scored: List[Tuple[int, Dict[str, Any]]] = []
    for r in records:
        text = f"{r.get('title','')} {r.get('description','')} {r.get('category','')} {r.get('season','')}".lower()
        score = sum(3 if w in safe_text(r.get('title')).lower() else 1 for w in words if w in text)
        if score:
            scored.append((score, r))
    scored.sort(key=lambda x: (-x[0], -int(x[1].get("opportunity_score") or 0)))
    return [r for _, r in scored]


def external_search(query: str) -> Tuple[List[Dict[str, Any]], pd.DataFrame]:
    started = time.perf_counter()
    rows: List[Dict[str, Any]] = []
    health: List[Tuple[str, str, int]] = []
    tasks = [(query, None), (query, "amazon"), (query, "ebay"), (query, "aliexpress"), (query, "jbhifi"), (query, "shein")]
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_lianex_query, q, marketplace): marketplace for q, marketplace in tasks}
        for future in as_completed(futures):
            marketplace = futures[future]
            try:
                r, status = future.result()
            except Exception as exc:
                r, status = [], f"collector error: {type(exc).__name__}"
            rows.extend(r)
            health.append((f"Lianex/{marketplace or 'general'}", status, len(r)))
    rows = exact_url_dedupe(rows)
    return rows, build_health(health, started)


def render_product_card(record: Dict[str, Any], favorites: set) -> None:
    pid = record["product_id"]
    title = safe_text(record.get("title"))
    image = normalize_url(record.get("image_url"))
    source = safe_text(record.get("source"))
    price = safe_text(record.get("price"))
    currency = safe_text(record.get("currency"))
    summary = safe_text(record.get("description")) or "Real public product listing."
    if len(summary) > 180:
        summary = summary[:177] + "..."
    season = safe_text(record.get("season"))
    category = safe_text(record.get("category"))
    trend_status = safe_text(record.get("trend_status"))
    opportunity = record.get("opportunity_score")
    usefulness = record.get("usefulness_score")
    uniqueness = record.get("uniqueness_score")

    with st.container(border=True):
        if image:
            # Browser-side image load avoids Streamlit server-side image proxy failures.
            escaped = html.escape(image, quote=True)
            st.markdown(
                f'<div class="ph-img"><img src="{escaped}" alt="{html.escape(title, quote=True)}" loading="lazy"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="ph-img ph-noimg">Product image not available</div>', unsafe_allow_html=True)
        badges = f'<span class="ph-badge">{html.escape(trend_status)}</span> <span class="ph-badge">{html.escape(category)}</span>'
        if season and season != "All-Year":
            badges += f' <span class="ph-badge">{html.escape(season)}</span>'
        st.markdown(badges, unsafe_allow_html=True)
        st.markdown(f"**{html.escape(title)}**", unsafe_allow_html=True)
        meta = source
        if price:
            meta += f" · {price} {currency}".strip()
        st.caption(meta)
        st.write(summary)
        st.write(f"**{int(opportunity or 0)}/100 opportunity**")
        st.caption(f"Usefulness {int(usefulness or 0)} · Uniqueness {int(uniqueness or 0)}")

        c1, c2, c3 = st.columns([1, 2, 2])
        with c1:
            is_fav = pid in favorites
            if st.button("♥" if is_fav else "♡", key=f"fav_{pid}", width="stretch"):
                if is_fav:
                    favorites.remove(pid)
                else:
                    favorites.add(pid)
                st.rerun()
        with c2:
            st.link_button("▶ YouTube", record["youtube_reference_url"], width="stretch")
        with c3:
            st.link_button("◎ Instagram", record["instagram_reference_url"], width="stretch")

        with st.expander(f"🛒 Product links ({len(record.get('product_links') or []) + 1})"):
            st.link_button(f"Open exact product — {source}", record["canonical_url"], width="stretch")
            st.caption("The links below are marketplace search links, not guaranteed exact matches.")
            for name, url, kind in record.get("product_links") or []:
                st.link_button(f"{name} search", url, width="stretch")


def apply_filters(records: List[Dict[str, Any]], season: str, category: str, trend: str, sort_name: str) -> List[Dict[str, Any]]:
    rows = records
    if season != "All Seasons":
        rows = [r for r in rows if season.lower() in safe_text(r.get("season")).lower()]
    if category != "All":
        rows = [r for r in rows if safe_text(r.get("category")) == category]
    if trend != "All":
        rows = [r for r in rows if safe_text(r.get("trend_status")) == trend]
    if sort_name == "Opportunity":
        rows = sorted(rows, key=lambda r: -(int(r.get("opportunity_score") or 0)))
    elif sort_name == "Usefulness":
        rows = sorted(rows, key=lambda r: -(int(r.get("usefulness_score") or 0)))
    elif sort_name == "Uniqueness":
        rows = sorted(rows, key=lambda r: -(int(r.get("uniqueness_score") or 0)))
    elif sort_name == "Newest checked":
        rows = sorted(rows, key=lambda r: safe_text(r.get("last_checked_at")), reverse=True)
    return rows


def render_trending_stars() -> None:
    st.subheader("⭐ Trending Stars")
    st.write("Trend/research sources are kept separate from the product catalog. Social content is opened for research only; the app does not download or republish videos/posts.")
    cols = st.columns(3)
    targets = [
        ("▶ YouTube", "https://www.youtube.com/results?search_query=trending+products+gadgets"),
        ("◎ Instagram", "https://www.instagram.com/explore/tags/gadgets/"),
        ("♪ TikTok", "https://www.tiktok.com/search?q=trending%20products"),
        ("📌 Pinterest", "https://www.pinterest.com/search/pins/?q=trending%20products"),
        ("📈 Google Trends", "https://trends.google.com/trends/explore?q=products,gadgets"),
        ("🌐 Public web", "https://www.google.com/search?q=trending+products+gadgets"),
    ]
    for i, (label, url) in enumerate(targets):
        with cols[i % 3]:
            st.link_button(label, url, width="stretch")
    key = get_secret("YOUTUBE_API_KEY")
    if key:
        st.info("YouTube API key detected. The API is optional and does not replace the normal product search.")
    else:
        st.caption("Add YOUTUBE_API_KEY in Streamlit Secrets later for API-backed YouTube trend data. The hub works without it.")


def get_secret(name: str) -> str:
    try:
        if name in st.secrets:
            return safe_text(st.secrets[name])
    except Exception:
        pass
    return safe_text(os.environ.get(name))


def init_state() -> None:
    defaults = {
        "products": [], "health": [], "view": "feed", "page": 1, "search_term": "",
        "favorites": set(), "last_run": None, "search_health": [], "search_results": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def diagnostics_panel(health_records: List[Dict[str, Any]]) -> None:
    with st.expander("Source status & diagnostics"):
        if not health_records:
            st.write("No source diagnostics yet.")
            return
        df = pd.DataFrame(health_records)
        if not df.empty:
            df = df[[c for c in ["source", "status", "records", "seconds"] if c in df.columns]]
            st.dataframe(df, width="stretch", hide_index=True)
        st.caption("The feed uses structured product APIs first. A source failure does not invalidate records from other sources.")


def main() -> None:
    st.set_page_config(page_title="Product Hunter", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(
        """
        <style>
        .ph-img{height:250px;border-radius:14px;background:#f2f4f7;display:flex;align-items:center;justify-content:center;overflow:hidden;margin-bottom:10px}
        .ph-img img{width:100%;height:100%;object-fit:contain}
        .ph-noimg{color:#667085;font-size:14px}
        .ph-badge{display:inline-block;background:#eef2f6;border-radius:18px;padding:5px 10px;margin:0 4px 7px 0;font-size:12px}
        </style>
        """,
        unsafe_allow_html=True,
    )
    init_state()

    st.title("🔎 Product Hunter")
    st.caption("Real product discovery from structured public/partner-style catalogs. No demo products. Similar listings are not merged; exact duplicate URLs are removed.")

    top1, top2, top3, top4 = st.columns([5, 1.2, 1.8, 1.5])
    with top1:
        query = st.text_input("Search products, problems or gadgets", value=st.session_state.search_term, label_visibility="collapsed", placeholder="Search products, problems or gadgets…")
    with top2:
        search_clicked = st.button("🔎 Search", width="stretch")
    with top3:
        trend_clicked = st.button("⭐ Trending Stars", width="stretch")
    with top4:
        favorites_clicked = st.button(f"♥ Favorites ({len(st.session_state.favorites)})", width="stretch")

    if trend_clicked:
        st.session_state.view = "trends"
    if favorites_clicked:
        st.session_state.view = "favorites"
    if search_clicked:
        st.session_state.search_term = safe_text(query)
        st.session_state.page = 1
        if st.session_state.search_term:
            with st.spinner("Searching structured product sources…"):
                results, health = external_search(st.session_state.search_term)
            st.session_state.search_results = results
            st.session_state.search_health = health.to_dict("records")
        else:
            st.session_state.search_results = None
            st.session_state.view = "feed"

    if st.session_state.view == "trends":
        render_trending_stars()
        st.divider()
        if st.button("← Back to products", width="content"):
            st.session_state.view = "feed"
            st.rerun()
        return

    if st.session_state.view == "favorites":
        st.subheader("♥ Favorites")
        fav_rows = [r for r in st.session_state.products if r.get("product_id") in st.session_state.favorites]
        if not fav_rows:
            st.info("You have no saved products yet.")
        else:
            grid = [st.columns(3) for _ in range((len(fav_rows) + 2) // 3)]
            for idx, record in enumerate(fav_rows[:MAX_PRODUCTS]):
                with grid[idx // 3][idx % 3]:
                    render_product_card(record, st.session_state.favorites)
        if st.button("← Back to products", width="content"):
            st.session_state.view = "feed"
            st.rerun()
        return

    if not st.session_state.products:
        with st.spinner("Loading real products from structured public catalogs…"):
            rows, health = cached_global_products()
        st.session_state.products = rows
        st.session_state.health = health
        st.session_state.last_run = utc_now()

    st.session_state.health = st.session_state.health or []
    products = st.session_state.products

    if not products:
        st.error("No validated live product records were returned by the configured structured sources.")
        diagnostics_panel(st.session_state.health)
        if st.button("🔄 Refresh sources", width="content"):
            cached_global_products.clear()
            st.session_state.products = []
            st.session_state.health = []
            st.rerun()
        st.info("This build does not insert demo products to hide a data-source failure. Add a supported API/provider or retry when the public source is reachable.")
        return

    season_col, category_col, trend_col, sort_col = st.columns(4)
    with season_col:
        season = st.selectbox("Season", ["All Seasons"] + SEASONS, index=0)
    with category_col:
        category = st.selectbox("Category", ["All"] + CATEGORIES, index=0)
    with trend_col:
        trend = st.selectbox("Trend", ["All", "Trending", "Unverified"], index=0)
    with sort_col:
        sort_name = st.selectbox("Sort", ["Opportunity", "Usefulness", "Uniqueness", "Newest checked"], index=0)

    if st.session_state.search_results is not None:
        search_rows = st.session_state.search_results
        if not search_rows:
            search_rows = local_search(products, st.session_state.search_term)
            if search_rows:
                st.info(f"External source search found no direct matches, so the loaded real-product catalog was searched locally for ‘{st.session_state.search_term}’.")
        if not search_rows:
            st.warning(f"No matching real product records were found for ‘{st.session_state.search_term}’. No demo records were inserted.")
        rows = search_rows
        diagnostics_panel(st.session_state.search_health)
    else:
        rows = products
        diagnostics_panel(st.session_state.health)

    rows = apply_filters(rows, season, category, trend, sort_name)
    total = len(rows)
    max_pages = max(1, min(TOTAL_PAGES, (total + PAGE_SIZE - 1) // PAGE_SIZE))
    st.session_state.page = max(1, min(st.session_state.page, max_pages))
    start = (st.session_state.page - 1) * PAGE_SIZE
    page_rows = rows[start:start + PAGE_SIZE]

    c1, c2, c3 = st.columns(3)
    c1.metric("Real products loaded", len(products))
    c2.metric("Current results", total)
    c3.metric("Current page", f"{st.session_state.page} / {max_pages}")

    if not page_rows:
        st.info("No matching products on this page. Change the filters or search.")
    else:
        grid = [st.columns(3) for _ in range((len(page_rows) + 2) // 3)]
        for idx, record in enumerate(page_rows):
            with grid[idx // 3][idx % 3]:
                render_product_card(record, st.session_state.favorites)

    # Exactly one pagination control at the bottom.
    if max_pages > 1:
        nav_cols = st.columns(max_pages)
        for i in range(1, max_pages + 1):
            with nav_cols[i - 1]:
                if st.button(str(i), key=f"bottom_page_{i}", width="stretch"):
                    st.session_state.page = i
                    st.rerun()

    if st.session_state.products:
        st.divider()
        st.caption(f"{APP_VERSION} · {len(products)} real records in current result set · exact URL duplicates removed only · no demo catalog.")


if __name__ == "__main__":
    main()
