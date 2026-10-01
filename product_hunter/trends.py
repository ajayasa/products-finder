from __future__ import annotations

from urllib.parse import quote_plus

TREND_SOURCES = {
    'YouTube': 'https://www.youtube.com/results?search_query={q}',
    'Instagram': 'https://www.instagram.com/explore/search/keyword/?q={q}',
    'TikTok': 'https://www.tiktok.com/search?q={q}',
    'Pinterest': 'https://www.pinterest.com/search/pins/?q={q}',
    'Google Trends': 'https://trends.google.com/trends/explore?geo=IN&q={q}',
    'Public web': 'https://www.google.com/search?q={q}',
}


def trend_links(query: str) -> dict[str, str]:
    q = quote_plus(query.strip())
    return {name: template.format(q=q) for name, template in TREND_SOURCES.items()}
