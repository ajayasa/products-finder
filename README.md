# Global Product Hunter — Cloud v4

Mobile/desktop Streamlit app for social-first product discovery.

## Current capabilities
- Demo mode works without API keys.
- Live YouTube discovery using the official YouTube Data API v3.
- Recent-video filtering, view/like/comment enrichment, candidate grouping, category classification, trend velocity, saturation and opportunity scoring.
- Extracts purchase URLs found in video descriptions; otherwise provides an Amazon India product-search reference.
- Product thumbnails and original YouTube reference links.
- CSV export and responsive desktop/mobile layout.

## Streamlit Cloud
Repository root should contain `app.py` and `requirements.txt`. Add `YOUTUBE_API_KEY` through Streamlit Cloud App Settings/Secrets. Do not commit API keys to GitHub.

## Important
The app uses YouTube as a live social discovery source. Instagram broad public trend discovery is not implemented through an unrestricted scraper; a permitted Meta/public-web connector can be added separately. Reference content is not downloaded or republished.
