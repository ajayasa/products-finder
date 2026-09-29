import re
from .categories import classify
from .scoring import score_candidate
from .db import upsert_product, add_source

def product_key(name):
    return re.sub(r'[^a-z0-9]+','-',name.lower()).strip('-')[:120]

def ingest_youtube(items):
    out=[]
    for item in items:
        sn=item.get('snippet',{}); st=item.get('statistics',{})
        title=sn.get('title',''); desc=sn.get('description','')
        views=int(st.get('viewCount',0)); likes=int(st.get('likeCount',0)); comments=int(st.get('commentCount',0))
        scores=score_candidate(title,desc,views,likes,comments,source_count=1,creator_count=1)
        cat=classify(title+' '+desc)
        p={'product_key':product_key(title),'name':title,'category':cat,'segment':scores['status'] if scores['status']!='Rising' else 'Other','description':desc[:2000], 'image_url':sn.get('thumbnails',{}).get('high',{}).get('url',''), 'country':'', 'trend_status':scores['status'], **scores, 'why_interesting':'Discovered through recent YouTube product-related content; verify the actual product and social saturation before review.'}
        pid=upsert_product(p)
        vid=item.get('id','')
        add_source(pid,{'source_type':'YouTube','url':f'https://www.youtube.com/watch?v={vid}','title':title,'channel_or_account':sn.get('channelTitle',''),'views':views,'likes':likes,'comments':comments,'published_at':sn.get('publishedAt'),'verified':True})
        out.append(p)
    return out
