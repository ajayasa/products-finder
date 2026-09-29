from product_hunter.queries import QUERY_PACKS
from product_hunter.youtube import search_youtube
from product_hunter.ingest import ingest_youtube

for category, queries in QUERY_PACKS.items():
    for q in queries:
        try:
            items = search_youtube(q, days=30, max_results=10, region='IN')
            ingest_youtube(items)
            print(f'OK: {category} / {q}: {len(items)}')
        except Exception as e:
            print(f'ERROR: {category} / {q}: {e}')
