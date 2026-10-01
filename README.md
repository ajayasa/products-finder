# Product Hunter v16

Multi-source real-product discovery app for Streamlit Community Cloud.

## Included live sources

- Lianex public cached product catalogue API (no key required)
- Little Bird Electronics public read-only product API (no key required)

## Trend / reference sources

The **⭐ Trending Stars** area links to YouTube, Instagram, TikTok, Pinterest, Google Trends and public web research. The app does not download or republish social-media videos/posts.

## Important behavior

- No fake/demo products in the production feed.
- Similar products/listings are NOT merged.
- Only exact duplicate product URLs are removed.
- Navigation/legal/search/account pages are rejected.
- Each source is isolated; a failed source does not erase the others.
- Product cards include source, image when supplied, price when supplied, category, season, usefulness, uniqueness, product links, YouTube and Instagram research links.
- Marketplace links are explicitly labeled as search links when an exact cross-market listing was not discovered.
- Main feed supports up to 500 working records and five page controls with up to 100 cards per page.

## Streamlit Cloud

Repository root must contain `app.py` and `requirements.txt`.

No API key is required for the two initial product sources. Credentials for future provider-specific APIs should be stored in Streamlit Secrets, not GitHub.
