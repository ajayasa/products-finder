from __future__ import annotations

import html
import streamlit as st
import pandas as pd

from product_hunter.config import DEFAULT_QUERY_PACK, MAX_PRODUCTS
from product_hunter.sources import ProductCollector, Product
from product_hunter.trends import trend_links

st.set_page_config(page_title='Product Hunter', page_icon='🔎', layout='wide', initial_sidebar_state='collapsed')

# Stable session state initialization before any reads.
DEFAULT_STATE = {
    'products': [],
    'source_status': [],
    'query': '',
    'page': 1,
    'view': 'products',
    'favorites': set(),
    'loaded': False,
}
for key, value in DEFAULT_STATE.items():
    if key not in st.session_state:
        st.session_state[key] = value.copy() if isinstance(value, set) else value

st.markdown('''
<style>
.block-container {max-width: 1500px; padding-top: 1rem; padding-bottom: 3rem;}
.hero {padding: 0.5rem 0 1rem 0;}
.hero h1 {font-size: 2.35rem; margin: 0; letter-spacing: -0.03em;}
.hero p {color:#6b7280; margin:0.25rem 0 0 0;}
.badges {display:flex; flex-wrap:wrap; gap:.35rem; margin:.55rem 0 .7rem 0;}
.badge {display:inline-block; background:#f1f5f9; border-radius:999px; padding:.3rem .55rem; font-size:.78rem; color:#334155;}
.card {border:1px solid #e2e8f0; border-radius:16px; padding:.8rem; background:#fff; height:100%; box-shadow:0 1px 4px rgba(15,23,42,.05);}
.card img {width:100%; height:220px; object-fit:contain; background:#f8fafc; border-radius:12px;}
.title {font-weight:700; font-size:1.02rem; line-height:1.3; margin:.7rem 0 .35rem 0;}
.meta {font-size:.82rem; color:#64748b;}
.price {font-size:1.1rem; font-weight:750; margin:.45rem 0;}
.actions a {text-decoration:none;}
.small {font-size:.78rem; color:#64748b;}
.page-wrap {display:flex; justify-content:center; gap:.35rem; margin:1.25rem 0 0 0;}
.page-num {border:1px solid #cbd5e1; border-radius:8px; padding:.25rem .55rem; font-size:.78rem; text-decoration:none; color:#334155;}
.page-num.active {font-weight:700; background:#f1f5f9;}
</style>
''', unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🔎 Product Hunter</h1><p>Real product discovery from multiple structured/public catalogs. Similar listings are not merged; only exact duplicate URLs are removed.</p></div>', unsafe_allow_html=True)

# Search + requested action buttons on same row.
c1, c2, c3, c4 = st.columns([5.8, 1.35, 1.8, 1.45], vertical_alignment='center')
with c1:
    q = st.text_input('Search products', value=st.session_state.query, placeholder='Search products, problems or gadgets…', label_visibility='collapsed')
with c2:
    do_search = st.button('🔎 Search', use_container_width=True)
with c3:
    trending = st.button('⭐ Trending Stars', use_container_width=True)
with c4:
    fav = st.button(f'♥ Favorites ({len(st.session_state.favorites)})', use_container_width=True)

if do_search:
    st.session_state.query = q.strip()
    st.session_state.page = 1
    st.session_state.view = 'products'
    st.session_state.loaded = False

if trending:
    st.session_state.view = 'trending'
if fav:
    st.session_state.view = 'favorites'

f1, f2, f3, f4 = st.columns([1.2, 1.2, 1.2, 1.2])
with f1:
    season = st.selectbox('Season', ['All Seasons','Summer','Monsoon','Winter','Sankranti','Ugadi','Dasara / Dussehra','Diwali','Christmas / New Year','Wedding season','School / college reopening','Travel season'])
with f2:
    category = st.selectbox('Category', ['All'] + ['Unique & Clever','Problem-Solving','Home & Kitchen','Tech & Gadgets','Car & Bike','Travel','Personal Use & Grooming','Village / Rural','Farming & Agriculture','Seasonal','Outdoor & Garden','Tools & DIY','Cleaning & Organization','Safety & Emergency','Kids & Parents','Elderly / Senior-Friendly','Office & Work From Home','Money-Saving','Local / Indian-Specific'])
with f3:
    trend = st.selectbox('Trend', ['All','Viral / Trending','Rising','Other','Unverified'])
with f4:
    sort = st.selectbox('Sort', ['Opportunity','Newest source order','Usefulness','Uniqueness','Price low → high'])

@st.cache_data(ttl=900, show_spinner=False)
def load_products(query: str):
    collector = ProductCollector()
    queries = [query] if query else DEFAULT_QUERY_PACK
    lianex = collector.collect_lianex(queries, per_query=40)
    little = collector.collect_little_bird(queries[:5], per_query=25, max_pages=3)
    products = collector.exact_url_dedupe(lianex + little)
    return products[:MAX_PRODUCTS], [(s.name, s.ok, s.count, s.message) for s in collector.status]

if not st.session_state.loaded and st.session_state.view in {'products','favorites'}:
    with st.spinner('Loading real products from configured sources…'):
        products, statuses = load_products(st.session_state.query)
        st.session_state.products = products
        st.session_state.source_status = statuses
        st.session_state.loaded = True

with st.expander('Source status & diagnostics', expanded=False):
    if st.session_state.source_status:
        for name, ok, count, message in st.session_state.source_status:
            icon = '✅' if ok else '⚠️'
            st.write(f'{icon} **{name}** — {message}')
    else:
        st.write('No source collection has run yet.')

if st.session_state.view == 'trending':
    st.subheader('⭐ Trending Stars')
    st.caption('Trend/reference research is separate from product discovery. The app opens public reference pages; it does not download or republish social media media.')
    trend_query = st.text_input('Trend topic', value=st.session_state.query or 'useful gadgets')
    links = trend_links(trend_query)
    cols = st.columns(3)
    for i, (name, url) in enumerate(links.items()):
        with cols[i % 3]:
            st.link_button(name, url, use_container_width=True)
    st.info('Actual API-based trend metrics can be connected per provider where access is available. The interface does not fabricate a trend score when verified trend data is absent.')
    st.stop()

products: list[Product] = st.session_state.products
if st.session_state.view == 'favorites':
    products = [p for p in products if p.product_id in st.session_state.favorites]

if st.session_state.query:
    qlower = st.session_state.query.lower()
    products = [p for p in products if qlower in f'{p.name} {p.description} {p.brand} {p.category}'.lower()]

if season != 'All Seasons':
    products = [p for p in products if season in p.seasons]
if category != 'All':
    products = [p for p in products if p.category == category]
if trend != 'All':
    products = [p for p in products if p.trend_status == trend]

if sort == 'Opportunity':
    products = sorted(products, key=lambda x: (x.opportunity_score if x.opportunity_score is not None else -1), reverse=True)
elif sort == 'Usefulness':
    products = sorted(products, key=lambda x: x.usefulness_score, reverse=True)
elif sort == 'Uniqueness':
    products = sorted(products, key=lambda x: x.uniqueness_score, reverse=True)
elif sort == 'Price low → high':
    products = sorted(products, key=lambda x: float(str(x.price).replace(',','')) if str(x.price).replace(',','').replace('.','',1).isdigit() else 10**18)

st.write(f'**{len(products)} products**')

page_size = 100
pages = max(1, min(5, (len(products) + page_size - 1) // page_size))
st.session_state.page = min(st.session_state.page, pages)
start = (st.session_state.page - 1) * page_size
page_products = products[start:start + page_size]

if not page_products:
    st.warning('No valid product listings match the current filters. Open Source status & diagnostics to see which sources responded.')
else:
    for row_start in range(0, len(page_products), 3):
        cols = st.columns(3)
        for col, product in zip(cols, page_products[row_start:row_start+3]):
            with col:
                img = product.image_url
                if img:
                    st.image(img, use_container_width=True)
                else:
                    st.markdown('<div style="height:220px;border-radius:12px;background:#f8fafc;display:flex;align-items:center;justify-content:center;color:#64748b">Product image not available</div>', unsafe_allow_html=True)
                st.markdown('<div class="badges">' + ''.join(f'<span class="badge">{html.escape(b)}</span>' for b in [product.trend_status, product.category, *product.seasons]) + '</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="title">{html.escape(product.name)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="meta">Source: {html.escape(product.source)}' + (f' · Brand: {html.escape(product.brand)}' if product.brand else '') + '</div>', unsafe_allow_html=True)
                if product.price:
                    st.markdown(f'<div class="price">{html.escape(product.currency)} {html.escape(product.price)}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="small">Usefulness {product.usefulness_score}/100 · Uniqueness {product.uniqueness_score}/100 · Opportunity {product.opportunity_score if product.opportunity_score is not None else "—"}</div>', unsafe_allow_html=True)
                if product.description:
                    st.caption(product.description[:220] + ('…' if len(product.description) > 220 else ''))
                is_fav = product.product_id in st.session_state.favorites
                if st.button('♥' if is_fav else '♡', key=f'fav_{product.product_id}', help='Save favorite'):
                    if is_fav:
                        st.session_state.favorites.remove(product.product_id)
                    else:
                        st.session_state.favorites.add(product.product_id)
                    st.rerun()
                a1, a2 = st.columns(2)
                with a1:
                    st.link_button('▶ YouTube', product.youtube_url, use_container_width=True)
                with a2:
                    st.link_button('◎ Instagram', product.instagram_url, use_container_width=True)
                with st.expander('Product links'):
                    for label, url in product.direct_links.items():
                        st.link_button(f'Exact: {label}', url, use_container_width=True)
                    st.caption('Marketplace links below are search links unless marked Exact.')
                    for label, url in product.product_links.items():
                        st.link_button(f'Search: {label}', url, use_container_width=True)
                with st.expander('Details'):
                    st.write(product.description or 'No description supplied by source.')
                    st.write(f'Availability: {product.availability or "Not supplied"}')

# Small bottom pagination only.
pages = max(1, min(5, (len(products) + page_size - 1) // page_size))
buttons = []
for n in range(1, 6):
    disabled = n > pages
    label = str(n)
    if disabled:
        st.button(label, key=f'page_disabled_{n}', disabled=True)
    else:
        if st.button(label, key=f'page_{n}', type='primary' if n == st.session_state.page else 'secondary'):
            st.session_state.page = n
            st.rerun()
