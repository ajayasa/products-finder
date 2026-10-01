from __future__ import annotations

import os

DEFAULT_LIANEX_URL = 'https://api.lianex.ai/api/public/search'
DEFAULT_LITTLE_BIRD_URL = 'https://littlebirdelectronics.com.au/public-api/v1/products'

DEFAULT_QUERY_PACK = [
    'useful gadgets', 'problem solving products', 'innovative products',
    'smart home gadget', 'kitchen gadget', 'travel gadget',
    'car accessory', 'bike accessory', 'farming tool',
    'garden tool', 'cleaning gadget', 'organization product',
]

MARKETPLACE_SEARCH_URLS = {
    'Amazon India': 'https://www.amazon.in/s?k={q}',
    'Amazon': 'https://www.amazon.com/s?k={q}',
    'Flipkart': 'https://www.flipkart.com/search?q={q}',
    'Meesho': 'https://www.meesho.com/search?q={q}',
    'eBay': 'https://www.ebay.com/sch/i.html?_nkw={q}',
    'AliExpress': 'https://www.aliexpress.com/w/wholesale-{slug}.html',
    'Alibaba': 'https://www.alibaba.com/trade/search?SearchText={q}',
    'Etsy': 'https://www.etsy.com/search?q={q}',
    'Walmart': 'https://www.walmart.com/search?q={q}',
    'Target': 'https://www.target.com/s?searchTerm={q}',
    'Best Buy': 'https://www.bestbuy.com/site/searchpage.jsp?st={q}',
    'Ubuy': 'https://www.google.com/search?q=site%3Aubuy.com+{q}',
    'IndiaMART': 'https://dir.indiamart.com/search.mp?ss={q}',
    'Temu': 'https://www.google.com/search?q=site%3Atemu.com+{q}',
    'Shopee': 'https://www.google.com/search?q=site%3Ashopee.com+{q}',
    'Lazada': 'https://www.google.com/search?q=site%3Alazada.com+{q}',
}

TARGET_MARKETPLACES = list(MARKETPLACE_SEARCH_URLS)

BLOCKED_TITLE_TERMS = {
    'terms', 'privacy', 'cookie', 'sign in', 'login', 'contact us', 'help',
    'about us', 'account', 'checkout', 'cart', 'category', 'categories',
    'search results', 'seller center', 'store locator', 'shipping policy',
}

BLOCKED_URL_TERMS = {
    '/terms', '/privacy', '/cookies', '/login', '/signin', '/sign-in',
    '/account', '/checkout', '/cart', '/help', '/contact', '/about',
    '/category/', '/categories/', '/search?', '/search/', '/seller/',
}

USER_AGENT = 'ProductHunter/17.0 (Streamlit Cloud)'
TIMEOUT_SECONDS = 15
MAX_PRODUCTS = 500

LIANEX_MARKETPLACES = {
    'ebay': 'eBay',
    'amazon': 'Amazon',
    'aliexpress': 'AliExpress',
    'jbhifi': 'JB Hi-Fi',
    'shein': 'SHEIN',
}

EBAY_TOKEN_URL = 'https://api.ebay.com/identity/v1/oauth2/token'
EBAY_BROWSE_URL = 'https://api.ebay.com/buy/browse/v1/item_summary/search'
ETSY_LISTINGS_URL = 'https://openapi.etsy.com/v3/application/listings/active'
WALMART_SEARCH_URL = 'https://marketplace.walmartapis.com/v3/items/walmart/search'

