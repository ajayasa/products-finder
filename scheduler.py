import time, schedule
from discover import QUERY_PACKS
from product_hunter.youtube import search_youtube
from product_hunter.ingest import ingest_youtube

def job():
    for queries in QUERY_PACKS.values():
        for q in queries:
            try:
                ingest_youtube(search_youtube(q, days=7, max_results=10, region='IN'))
            except Exception as e:
                print('Discovery error:', q, e)

schedule.every().day.at('09:00').do(job)
print('Product Hunter scheduler running. Daily discovery at 09:00 local machine time.')
while True:
    schedule.run_pending()
    time.sleep(30)
