# Product Hunter v27

Product Hunter is a Streamlit product-discovery application designed to show real public product listings without using fake/demo records.

## Data architecture

The primary discovery adapter uses the documented Lianex public read API. It is a structured cache-only product API with no API key requirement. Its documented public search supports product title, price, currency, image, marketplace/provider, availability and URL fields. The app never treats the Lianex cache as a live marketplace crawl; it treats it as a structured external product-data source.

A second structured adapter uses Little Bird Electronics' documented public JSON catalog API. It is a read-only public catalog and provides product images and pricing without authentication. It is used as a resilience/source-diversity fallback.

Optional credentials can be added later through Streamlit Secrets. The app does not require API keys for the baseline structured product feed.

## Production behavior

- No fake/demo products are inserted into the production feed.
- Legal, navigation, account, search and category pages are rejected.
- Similar products are not merged.
- Only exact normalized product URL duplicates are removed.
- Product images are shown from the actual source image URL when provided.
- Missing source images remain a neutral missing-image state.
- Normal Search always searches product sources and can fall back to the already-loaded real catalog.
- Trending Stars is a separate research hub for YouTube, Instagram, TikTok, Pinterest, Google Trends and public web search.
- The feed supports five pages with up to 100 records per page, up to 500 records in the standard result set.
- Source failures are isolated and shown in diagnostics.
- No secrets are hard-coded.

## Streamlit Community Cloud

Set the repository to the project root and the main file to `app.py`. Streamlit Community Cloud supports dependency installation from `requirements.txt` and secure secrets through the app's Advanced settings.

No `.streamlit/secrets.toml` file is required for the baseline data feed.

Optional:

YOUTUBE_API_KEY = "..."

This key is only for future/API-backed trend enrichment. It does not alter the normal product Search behavior.

## Important limitation

The app cannot guarantee access to every marketplace on every day. Marketplaces can restrict automated access or change their public interfaces. This build therefore prioritizes structured public product-data APIs and source isolation instead of relying on anonymous HTML scraping as the only production path.
