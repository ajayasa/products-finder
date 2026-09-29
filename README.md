# Global Product Hunter — MVP

A social-first product discovery dashboard for a product-review YouTube channel.

## What it does
- Searches YouTube using the official YouTube Data API v3.
- Accepts public Instagram/Reel URLs as research references.
- Stores product records in SQLite.
- Categorizes products into the channel's category tree.
- Separates Viral/Trending, Rising, and Other.
- Scores uniqueness, usefulness, visual/demo potential, trend momentum, saturation, India relevance and seasonal relevance.
- Stores product links, source links and image URLs.
- Deduplicates products by normalized name.
- Exports CSV.
- Provides a dashboard for filtering and reviewing candidates.

## Important platform note
This MVP does not download or republish other creators' videos. YouTube/Instagram links are reference sources only. Public platform access varies; Instagram is intentionally treated as a reference/public-source layer rather than assuming unrestricted access to all Reel data.

## Run locally
1. Install Python 3.11+.
2. Create a virtual environment.
3. Install requirements: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`.
5. Add a YouTube Data API v3 key to `YOUTUBE_API_KEY`.
6. Run: `streamlit run app.py`
7. Open the local URL shown by Streamlit.

## YouTube API
The app uses `search.list` to discover videos and `videos.list` to enrich results with statistics. See Google's official documentation for API setup and quota details.

## Project structure
- `app.py` — Streamlit dashboard
- `product_hunter/` — discovery, scoring, categorization and storage
- `data/` — SQLite database created automatically
- `.env.example` — configuration template
- `requirements.txt` — dependencies

## Next production steps
- Add scheduled background discovery.
- Add permitted Instagram/public-web connectors.
- Add marketplace/product-source verification adapters.
- Add image extraction with source attribution.
- Add trend history so velocity is calculated from repeated observations.
- Add notifications for new high-score products.

## Automated discovery
- `discover.py` runs the complete query pack once.
- `scheduler.py` runs the query pack daily at 09:00 local machine time.
- `seed_demo.py` inserts sample records so you can inspect the dashboard before connecting an API.

## Recommended production architecture
The MVP deliberately keeps connectors separate. YouTube is the first live connector. Instagram/public web connectors should be added only through permitted APIs/publicly accessible sources. Product-source adapters can then enrich each social discovery with official product pages and purchase links.
