# Product Hunter v17

This version continues the working Product Hunter feed and expands the product-source layer.

## Product sources

The main feed uses real catalog data from multiple independent sources:

- Lianex cache, queried separately for its currently documented marketplaces: eBay, Amazon, AliExpress, JB Hi-Fi and SHEIN. Lianex is cache-only and does not perform live marketplace searches.
- Little Bird Electronics public read-only JSON API.
- Optional official eBay Browse API when `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` are configured.
- Optional Etsy Open API when `ETSY_API_KEY` is configured.
- Optional Walmart API when `WALMART_ACCESS_TOKEN` is configured.

Similar listings are not merged. Only exact normalized duplicate URLs are removed after all sources are collected.

Other marketplace links remain available as search links when an exact listing was not actually discovered. The UI labels exact product links separately from marketplace search links.

## Streamlit Cloud secrets

Optional provider secrets can be entered in the Streamlit Cloud app settings under Secrets. The app reads:

```toml
EBAY_CLIENT_ID = "..."
EBAY_CLIENT_SECRET = "..."
ETSY_API_KEY = "..."
WALMART_ACCESS_TOKEN = "..."
```

No secrets are hard-coded.

## Trend sources

The separate `⭐ Trending Stars` area opens public research/reference pages for YouTube, Instagram, TikTok, Pinterest, Google Trends and the public web. Social media is not downloaded or republished.

## Run

Streamlit Cloud entry point: `app.py`.

No Bash-only deployment workflow is required.
