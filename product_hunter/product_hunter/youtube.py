import requests
from datetime import datetime, timedelta, timezone
from .config import YOUTUBE_API_KEY

def search_youtube(query, days=30, max_results=25, region='IN'):
    if not YOUTUBE_API_KEY:
        raise RuntimeError('YOUTUBE_API_KEY is not configured')
    published_after = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace('+00:00','Z')
    params = {'part':'snippet','q':query,'type':'video','order':'date','maxResults':min(max_results,50),'publishedAfter':published_after,'regionCode':region,'key':YOUTUBE_API_KEY}
    r=requests.get('https://www.googleapis.com/youtube/v3/search',params=params,timeout=30); r.raise_for_status()
    items=r.json().get('items',[])
    ids=[x['id']['videoId'] for x in items if x.get('id',{}).get('videoId')]
    if not ids: return []
    p={'part':'snippet,statistics,contentDetails','id':','.join(ids),'key':YOUTUBE_API_KEY}
    vr=requests.get('https://www.googleapis.com/youtube/v3/videos',params=p,timeout=30); vr.raise_for_status()
    return vr.json().get('items',[])
