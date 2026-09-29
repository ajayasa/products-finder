from product_hunter.db import upsert_product, add_source
samples = [
 {'product_key':'demo-foldable-food-sealer','name':'Demo Foldable Food Sealer','category':'Home & Kitchen','segment':'Other','description':'Demo record for testing the dashboard.','product_url':'https://example.com/product','image_url':'https://placehold.co/600x400/png?text=Product','country':'India','price':'','india_availability':'Unknown','trend_status':'Rising','trend_score':62,'uniqueness_score':76,'usefulness_score':84,'demo_score':88,'saturation_score':34,'india_relevance':90,'opportunity_score':79,'why_interesting':'Clear visual problem/solution demonstration.'},
 {'product_key':'demo-smart-soil-meter','name':'Demo Smart Soil Meter','category':'Farming & Agriculture','segment':'Other','description':'Demo record for testing the dashboard.','product_url':'https://example.com/product','image_url':'https://placehold.co/600x400/png?text=Farming','country':'India','price':'','india_availability':'Unknown','trend_status':'Other','trend_score':38,'uniqueness_score':90,'usefulness_score':92,'demo_score':86,'saturation_score':20,'india_relevance':94,'opportunity_score':82,'why_interesting':'Strong niche utility and easy live demonstration.'}
]
for p in samples:
    pid=upsert_product(p)
    add_source(pid, {'source_type':'Demo','url':'https://example.com','title':'Demo reference','channel_or_account':'Demo','verified':False})
print('Demo data inserted.')
