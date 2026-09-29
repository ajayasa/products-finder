import os, re, math, html
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
import json
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Product Hunter", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")

PAGE_SIZE = 100
TOTAL_PAGES = 5
MAX_CARDS = PAGE_SIZE * TOTAL_PAGES
ASSET_DIR = Path(__file__).parent / "assets"

# Architecture: the base catalog is web-first and source-agnostic.
# Product sources are independent of trend sources; trend signals are optional enrichment.
PRODUCT_SOURCE_REGISTRY = [
    "Amazon", "Flipkart", "Meesho", "eBay", "AliExpress", "Alibaba", "Etsy",
    "Walmart", "Target", "Best Buy", "Ubuy", "IndiaMART", "Brand / Manufacturer Sites",
    "Regional & Country-Specific Marketplaces", "Other Public Product Websites"
]
TREND_SOURCE_REGISTRY = [
    "YouTube", "Instagram", "TikTok", "Pinterest", "Google Trends", "Public Web Signals"
]

CATEGORIES = [
    "Unique & Clever", "Problem-Solving", "Home & Kitchen", "Tech & Gadgets", "Car & Bike",
    "Travel", "Personal Use & Grooming", "Village / Rural", "Farming & Agriculture", "Seasonal",
    "Outdoor & Garden", "Tools & DIY", "Cleaning & Organization", "Safety & Emergency",
    "Kids & Parents", "Elderly / Senior-Friendly", "Office & Work From Home", "Money-Saving", "Local / Indian-Specific"
]

QUERY_PACK = {
    "Unique & Clever": ["clever useful gadgets", "things I didn't know existed", "innovative useful products"],
    "Problem-Solving": ["problem solving products", "life changing useful gadgets", "smart problem solving tools"],
    "Home & Kitchen": ["viral kitchen gadgets", "useful home gadgets", "kitchen inventions"],
    "Tech & Gadgets": ["new useful tech gadgets", "innovative electronics", "smart gadgets worth buying"],
    "Car & Bike": ["useful car gadgets", "useful bike gadgets", "car accessories worth buying"],
    "Travel": ["travel gadgets", "airport travel products", "travel problem solving products"],
    "Personal Use & Grooming": ["useful grooming gadgets", "personal care gadgets", "viral grooming products"],
    "Village / Rural": ["village useful products", "rural tools", "Indian village gadgets"],
    "Farming & Agriculture": ["useful farming tools", "agriculture gadgets", "farm inventions"],
    "Seasonal": ["summer useful products", "monsoon useful products", "festival useful products"],
    "Outdoor & Garden": ["garden tools", "outdoor useful gadgets", "camping gadgets"],
    "Tools & DIY": ["useful DIY tools", "clever hand tools", "workshop gadgets"],
    "Cleaning & Organization": ["cleaning gadgets", "home organization products", "storage hacks products"],
    "Safety & Emergency": ["emergency gadgets", "safety products", "roadside emergency gadgets"],
    "Kids & Parents": ["useful parenting gadgets", "kids useful products", "parenting problem solving products"],
    "Elderly / Senior-Friendly": ["senior friendly gadgets", "elderly useful products", "easy use home gadgets"],
    "Office & Work From Home": ["work from home gadgets", "office desk gadgets", "productivity gadgets"],
    "Money-Saving": ["money saving products", "products that save money", "reusable useful products"],
    "Local / Indian-Specific": ["Indian household useful products", "Indian kitchen gadgets", "Indian daily use products"],
}

SEASONAL_TERMS = {
    "Summer": ["summer", "heat", "cooling", "hot weather", "sun", "ice"],
    "Monsoon": ["monsoon", "rain", "waterproof", "rainy", "drain", "mold"],
    "Winter": ["winter", "cold", "warm", "heater", "blanket"],
    "Sankranti": ["sankranti", "pongal", "kite", "rangoli"],
    "Ugadi": ["ugadi", "festival", "panchanga"],
    "Dasara": ["dasara", "dussehra", "navratri"],
    "Diwali": ["diwali", "deepavali", "lights", "rangoli", "festival"],
    "Christmas / New Year": ["christmas", "new year", "gift", "party"],
    "Wedding Season": ["wedding", "marriage", "bride", "groom"],
    "School / College": ["school", "college", "student", "back to school", "study"],
    "Travel Season": ["travel", "holiday", "vacation", "trip", "airport"],
}

KEYWORDS = {
 "Farming & Agriculture":"farm farmer farming agriculture soil seed crop sprayer weeder irrigation fertilizer pesticide transplanter harvest",
 "Village / Rural":"village rural desi indian village gaon rural home",
 "Car & Bike":"car bike motorcycle scooter tyre tire dashcam car accessory helmet",
 "Travel":"travel camping luggage airport flight road trip portable travel gadget",
 "Home & Kitchen":"kitchen cooking food home organizer storage chopper cutter sealer dispenser",
 "Tech & Gadgets":"gadget smart phone mobile charger usb bluetooth camera electronics keyboard mouse",
 "Tools & DIY":"tool diy drill repair workshop wrench screwdriver cutter",
 "Outdoor & Garden":"garden outdoor camping patio plant lawn gardening",
 "Personal Use & Grooming":"grooming shaver trimmer hair beauty personal care",
 "Cleaning & Organization":"cleaning organizer storage vacuum mop laundry",
 "Safety & Emergency":"safety emergency first aid alarm reflective roadside rescue",
 "Office & Work From Home":"office desk work from home productivity laptop monitor",
 "Kids & Parents":"kids baby toddler parent parenting school",
 "Elderly / Senior-Friendly":"elderly senior old easy grip mobility home",
 "Money-Saving":"save money reusable refill energy saving economical",
 "Seasonal":"summer monsoon winter diwali sankranti ugadi dasara christmas wedding school",
 "Local / Indian-Specific":"india indian telugu tamil kitchen household village desi",
 "Problem-Solving":"problem solving fix solution hack useful",
 "Unique & Clever":"clever innovative invention unusual unique smart",
}


def clean_text(x):
    return re.sub(r"\s+", " ", html.unescape(str(x or ""))).strip()


def classify(text):
    t=clean_text(text).lower()
    scored=[(sum(1 for w in words.split() if w in t), cat) for cat,words in KEYWORDS.items()]
    best=max(scored)
    return best[1] if best[0] else "Unique & Clever"


def seasonal_tag(text):
    t=clean_text(text).lower()
    return ", ".join(season for season,words in SEASONAL_TERMS.items() if any(w in t for w in words))


def extract_urls(text):
    urls=re.findall(r"https?://[^\s<>\]\)\"']+", text or "")
    out=[]
    for u in urls:
        u=u.rstrip(".,;!?)]}")
        host=urlparse(u).netloc.lower()
        if host and not any(x in host for x in ["youtube.com","youtu.be","instagram.com","facebook.com","tiktok.com","pinterest.com"]):
            out.append(u)
    return list(dict.fromkeys(out))


def marketplace_links(name):
    q=quote_plus(name)
    return [
        ["Amazon India",f"https://www.amazon.in/s?k={q}"],
        ["Amazon US",f"https://www.amazon.com/s?k={q}"],
        ["Flipkart",f"https://www.flipkart.com/search?q={q}"],
        ["Meesho",f"https://www.meesho.com/search?q={q}"],
        ["eBay",f"https://www.ebay.com/sch/i.html?_nkw={q}"],
        ["AliExpress",f"https://www.aliexpress.com/w/wholesale-{q}.html"],
        ["Alibaba",f"https://www.alibaba.com/trade/search?SearchText={q}"],
        ["Etsy",f"https://www.etsy.com/search?q={q}"],
        ["Walmart",f"https://www.walmart.com/search?q={q}"],
        ["Target",f"https://www.target.com/s?searchTerm={q}"],
        ["Best Buy",f"https://www.bestbuy.com/site/searchpage.jsp?st={q}"],
        ["Ubuy",f"https://www.ubuy.co.in/search/index/view?q={q}"],
        ["IndiaMART",f"https://dir.indiamart.com/search.mp?ss={q}"],
        ["Temu",f"https://www.temu.com/search_result.html?search_key={q}"],
        ["Shopee",f"https://shopee.com/search?keyword={q}"],
        ["Lazada",f"https://www.lazada.com/catalog/?q={q}"],
    ]


def candidate_name(title):
    t=clean_text(title)
    t=re.sub(r"\b(amazon|review|unboxing|testing|test|viral|must have|best|top|new|cool|useful|gadget|gadgets|product|products)\b", " ", t, flags=re.I)
    t=re.sub(r"[|•:]+", " ", t)
    t=re.sub(r"\([^)]*\)|\[[^]]*\]", " ", t)
    t=re.sub(r"\s+[-–—]\s+.*$", "", t)
    t=clean_text(t)
    return (t if len(t)>=5 else clean_text(title))[:90]


def score_video(v):
    views=max(int(v.get("views",0)),0); likes=max(int(v.get("likes",0)),0); comments=max(int(v.get("comments",0)),0)
    age=max(float(v.get("age_days",1)),0.25)
    velocity=math.log10(views+1)/math.log10(age+2)*18
    engagement=((likes+comments*3)/(views+1))*100
    trend=max(0,min(100,round(velocity*3.0 + min(engagement*2.5,25))))
    title=clean_text(v.get("title","" )).lower()
    usefulness=80 + (8 if any(w in title for w in ["useful","problem","solution","life changing","must have"]) else 0)
    demo=82 + (10 if any(w in title for w in ["how","test","testing","before after","hack","demo","try"]) else 0)
    uniqueness=84
    saturation=35
    opportunity=round(max(0,min(100,trend*.30+uniqueness*.22+min(usefulness,100)*.22+min(demo,100)*.16+(100-saturation)*.10)))
    status="Viral/Trending" if trend>=78 else ("Rising" if trend>=55 else "Other")
    return trend,uniqueness,min(usefulness,100),min(demo,100),saturation,opportunity,status


def normalize_product_name(name):
    t=clean_text(name).lower()
    t=re.sub(r"[^a-z0-9 ]+", " ", t)
    t=re.sub(r"\b(review|unboxing|amazon|flipkart|meesho|viral|best|top|new|cool|useful|gadget|gadgets|product|products)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def youtube_search_unique(api_key, query, region="IN", per_query=50):
    if not query.strip(): return pd.DataFrame()
    cutoff=(datetime.now(timezone.utc)-timedelta(days=90)).isoformat().replace("+00:00","Z")
    sess=requests.Session(); params={"part":"snippet","q":query.strip(),"type":"video","order":"relevance","publishedAfter":cutoff,"maxResults":min(int(per_query),50),"regionCode":region,"key":api_key}
    r=sess.get("https://www.googleapis.com/youtube/v3/search",params=params,timeout=20); r.raise_for_status()
    raw=[]
    for item in r.json().get("items",[]):
        vid=item.get("id",{}).get("videoId")
        if not vid: continue
        sn=item.get("snippet",{})
        raw.append({"video_id":vid,"title":sn.get("title",""),"description":sn.get("description","") or "","channel":sn.get("channelTitle",""),"published_at":sn.get("publishedAt",""),"thumbnail":sn.get("thumbnails",{}).get("high",{}).get("url") or sn.get("thumbnails",{}).get("medium",{}).get("url")})
    if not raw: return pd.DataFrame()
    ids=",".join(x["video_id"] for x in raw); r=sess.get("https://www.googleapis.com/youtube/v3/videos",params={"part":"snippet,statistics","id":ids,"key":api_key},timeout=20); r.raise_for_status()
    byid={x["video_id"]:x for x in raw}; rows=[]
    for item in r.json().get("items",[]):
        x=byid.get(item.get("id"),{}); stt=item.get("statistics",{}); pub=x.get("published_at","")
        try: age=(datetime.now(timezone.utc)-datetime.fromisoformat(pub.replace("Z","+00:00"))).total_seconds()/86400
        except: age=1
        x={**x,"views":int(stt.get("viewCount",0) or 0),"likes":int(stt.get("likeCount",0) or 0),"comments":int(stt.get("commentCount",0) or 0),"age_days":max(age,.25)}
        name=candidate_name(x["title"]); trend,uniq,use,demo,sat,opp,status=score_video(x); external=extract_urls(x.get("description","")); links=[[urlparse(u).netloc.replace("www.","").split(".")[0].title(),u] for u in external] or marketplace_links(name)
        rows.append({"name":name,"category":classify(name+" "+x.get("title","")+" "+x.get("description","")),"segment":"Viral / Trending Products" if status=="Viral/Trending" else "Other Unique & Useful","trend_status":status,"opportunity_score":opp,"trend_score":trend,"uniqueness_score":uniq,"usefulness_score":use,"demo_score":demo,"saturation_score":sat,"why_interesting":f"Reference video by {x.get('channel','creator')}; {x.get('views',0):,} views.","image_url":x.get("thumbnail","") or "","youtube_url":f"https://www.youtube.com/watch?v={x['video_id']}","instagram_url":f"https://www.instagram.com/explore/tags/{re.sub(r'[^a-z0-9]+','',name.lower())[:60]}/","product_links":links,"channel":x.get("channel",""),"views":x.get("views",0),"likes":x.get("likes",0),"comments":x.get("comments",0),"published_at":x.get("published_at",""),"season":seasonal_tag(name+" "+x.get("title",""))})
    return pd.DataFrame(rows).reset_index(drop=True)

def youtube_discover(api_key, region="IN", lookback=30, per_query=20, max_queries=20, language="en"):
    cutoff=(datetime.now(timezone.utc)-timedelta(days=lookback)).isoformat().replace("+00:00","Z")
    queries=[(cat,q) for cat,qs in QUERY_PACK.items() for q in qs][:max_queries]
    sess=requests.Session(); raw=[]
    for cat,q in queries:
        params={"part":"snippet","q":q,"type":"video","order":"date","publishedAfter":cutoff,"maxResults":min(int(per_query),50),"regionCode":region,"relevanceLanguage":language,"key":api_key}
        r=sess.get("https://www.googleapis.com/youtube/v3/search",params=params,timeout=20); r.raise_for_status()
        for item in r.json().get("items",[]):
            vid=item.get("id",{}).get("videoId")
            if not vid: continue
            sn=item.get("snippet",{})
            raw.append({"video_id":vid,"title":sn.get("title",""),"description":sn.get("description","") or "","channel":sn.get("channelTitle",""),"published_at":sn.get("publishedAt",""),"thumbnail":sn.get("thumbnails",{}).get("high",{}).get("url") or sn.get("thumbnails",{}).get("medium",{}).get("url"),"query_category":cat})
    # Remove only repeated copies of the exact same video ID. Product duplicates are intentionally retained.
    unique_by_video={x["video_id"]:x for x in raw}
    vids=list(unique_by_video.values())
    results=[]
    for i in range(0,len(vids),50):
        ids=",".join(x["video_id"] for x in vids[i:i+50])
        r=sess.get("https://www.googleapis.com/youtube/v3/videos",params={"part":"snippet,statistics","id":ids,"key":api_key},timeout=20); r.raise_for_status()
        for item in r.json().get("items",[]):
            base=unique_by_video.get(item.get("id"),{}); stt=item.get("statistics",{}); pub=base.get("published_at") or item.get("snippet",{}).get("publishedAt")
            try: age=(datetime.now(timezone.utc)-datetime.fromisoformat(pub.replace("Z","+00:00"))).total_seconds()/86400
            except: age=1
            results.append({**base,"views":int(stt.get("viewCount",0) or 0),"likes":int(stt.get("likeCount",0) or 0),"comments":int(stt.get("commentCount",0) or 0),"age_days":max(age,.25)})
    rows=[]
    for x in results[:MAX_CARDS]:
        name=candidate_name(x["title"]); trend,uniq,use,demo,sat,opp,status=score_video(x)
        cat=classify(name+" "+x.get("title","")+" "+x.get("description",""))
        external=extract_urls(x.get("description",""))
        product_links=[[urlparse(u).netloc.replace("www.","").split(".")[0].title(),u] for u in external]
        if not product_links: product_links=marketplace_links(name)
        instagram=[u for u in re.findall(r"https?://[^\s]+",x.get("description","") or "") if "instagram.com" in u.lower()]
        rows.append({"name":name,"category":cat,"segment":"Viral / Trending Products" if status=="Viral/Trending" else "Other Unique & Useful","trend_status":status,"opportunity_score":opp,"trend_score":trend,"uniqueness_score":uniq,"usefulness_score":use,"demo_score":demo,"saturation_score":sat,"why_interesting":f"Reference video by {x.get('channel','creator')}; {x.get('views',0):,} views, {x.get('likes',0):,} likes and {x.get('comments',0):,} comments.","image_url":x.get("thumbnail","") or "","youtube_url":f"https://www.youtube.com/watch?v={x['video_id']}","instagram_url":instagram[0] if instagram else f"https://www.instagram.com/explore/tags/{re.sub(r'[^a-z0-9]+','',name.lower())[:60]}/","product_links":product_links,"channel":x.get("channel",""),"views":x.get("views",0),"likes":x.get("likes",0),"comments":x.get("comments",0),"published_at":x.get("published_at",""),"season":seasonal_tag(name+" "+x.get("title",""))})
    return pd.DataFrame(rows)


def youtube_trends(api_key, region="IN", per_query=50):
    """Fetch a broad collection of current product/gadget trend videos. Exact duplicate videos are removed; product duplicates are retained."""
    if not api_key:
        return pd.DataFrame()
    trend_queries=[
        "trending products", "viral products", "trending gadgets", "viral gadgets",
        "must have products", "new useful products", "new gadgets", "viral kitchen gadgets",
        "viral home products", "viral car gadgets", "viral travel gadgets",
        "viral farming tools", "viral useful products"
    ]
    cutoff=(datetime.now(timezone.utc)-timedelta(days=30)).isoformat().replace("+00:00","Z")
    sess=requests.Session(); raw=[]
    for q in trend_queries:
        params={"part":"snippet","q":q,"type":"video","order":"viewCount","publishedAfter":cutoff,"maxResults":min(int(per_query),50),"regionCode":region,"relevanceLanguage":"en","key":api_key}
        r=sess.get("https://www.googleapis.com/youtube/v3/search",params=params,timeout=20); r.raise_for_status()
        for item in r.json().get("items",[]):
            vid=item.get("id",{}).get("videoId")
            if not vid: continue
            sn=item.get("snippet",{})
            raw.append({"video_id":vid,"title":sn.get("title",""),"description":sn.get("description","") or "","channel":sn.get("channelTitle",""),"published_at":sn.get("publishedAt",""),"thumbnail":sn.get("thumbnails",{}).get("high",{}).get("url") or sn.get("thumbnails",{}).get("medium",{}).get("url")})
    unique={x["video_id"]:x for x in raw}
    vids=list(unique.values()); rows=[]
    for i in range(0,len(vids),50):
        ids=",".join(x["video_id"] for x in vids[i:i+50])
        r=sess.get("https://www.googleapis.com/youtube/v3/videos",params={"part":"snippet,statistics","id":ids,"key":api_key},timeout=20); r.raise_for_status()
        for item in r.json().get("items",[]):
            base=unique.get(item.get("id"),{}); stt=item.get("statistics",{}); pub=base.get("published_at","")
            try: age=(datetime.now(timezone.utc)-datetime.fromisoformat(pub.replace("Z","+00:00"))).total_seconds()/86400
            except: age=1
            x={**base,"views":int(stt.get("viewCount",0) or 0),"likes":int(stt.get("likeCount",0) or 0),"comments":int(stt.get("commentCount",0) or 0),"age_days":max(age,.25)}
            name=candidate_name(x["title"]); trend,uniq_score,use,demo,sat,opp,status=score_video(x)
            external=extract_urls(x.get("description","")); links=[[urlparse(u).netloc.replace("www.","").split(".")[0].title(),u] for u in external] or marketplace_links(name)
            rows.append({"name":name,"category":classify(name+" "+x.get("title","")+" "+x.get("description","")),"segment":"Viral / Trending Products" if status=="Viral/Trending" else "Other Unique & Useful","trend_status":status,"opportunity_score":opp,"trend_score":trend,"uniqueness_score":uniq_score,"usefulness_score":use,"demo_score":demo,"saturation_score":sat,"why_interesting":f"Trending reference by {x.get('channel','creator')}; {x.get('views',0):,} views.","image_url":x.get("thumbnail","") or "","youtube_url":f"https://www.youtube.com/watch?v={item.get('id')}","instagram_url":f"https://www.instagram.com/explore/tags/{re.sub(r'[^a-z0-9]+','',name.lower())[:60]}/","product_links":links,"channel":x.get("channel",""),"views":x.get("views",0),"likes":x.get("likes",0),"comments":x.get("comments",0),"published_at":x.get("published_at",""),"season":seasonal_tag(name+" "+x.get("title",""))})
    return pd.DataFrame(rows).sort_values(["trend_score","views"],ascending=False).head(500).reset_index(drop=True) if rows else pd.DataFrame()

def instagram_trend_references(source_df):
    """Build public Instagram reference links from discovered product/trend titles without requesting Instagram credentials."""
    if source_df is None or source_df.empty: return pd.DataFrame()
    rows=[]
    for _,p in source_df.iterrows():
        name=clean_text(p.get("name","")); key=normalize_product_name(name)
        if not key: continue
        tag=re.sub(r"[^a-z0-9]+","",name.lower())[:60]
        rows.append({"name":name,"category":p.get("category","Unique & Clever"),"trend_status":p.get("trend_status","Rising"),"opportunity_score":p.get("opportunity_score",0),"trend_score":p.get("trend_score",0),"uniqueness_score":p.get("uniqueness_score",0),"usefulness_score":p.get("usefulness_score",0),"demo_score":p.get("demo_score",0),"saturation_score":p.get("saturation_score",0),"why_interesting":"Public Instagram reference search; no Instagram login or password is required.","image_url":p.get("image_url","") or "","youtube_url":p.get("youtube_url",f"https://www.youtube.com/results?search_query={quote_plus(name)}"),"instagram_url":f"https://www.instagram.com/explore/tags/{tag}/","product_links":p.get("product_links",[]) or marketplace_links(name),"channel":"Instagram public reference","views":p.get("views",0),"likes":p.get("likes",0),"comments":p.get("comments",0),"published_at":p.get("published_at","")})
    return pd.DataFrame(rows).head(500).reset_index(drop=True)



# Public-web product discovery: source-agnostic, API-optional collection layer.
PRODUCT_SOURCE_DOMAINS = {
    "Amazon": "amazon.com", "Amazon India": "amazon.in", "Flipkart": "flipkart.com", "Meesho": "meesho.com",
    "eBay": "ebay.com", "AliExpress": "aliexpress.com", "Alibaba": "alibaba.com", "Etsy": "etsy.com",
    "Walmart": "walmart.com", "Target": "target.com", "Best Buy": "bestbuy.com", "Ubuy": "ubuy.com",
    "IndiaMART": "indiamart.com", "Temu": "temu.com", "Shopee": "shopee.com", "Lazada": "lazada.com",
}


def _parse_search_html(html_text):
    rows=[]
    for block in re.findall(r'<li class="b_algo".*?</li>', html_text, flags=re.S|re.I):
        m=re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, flags=re.S|re.I)
        if not m: continue
        url=html.unescape(m.group(1)); title=clean_text(re.sub(r'<.*?>',' ',m.group(2)))
        sm=re.search(r'<p[^>]*>(.*?)</p>', block, flags=re.S|re.I)
        snippet=clean_text(re.sub(r'<.*?>',' ',sm.group(1))) if sm else ""
        if url.startswith("http"): rows.append({"url":url,"title":title,"snippet":snippet})
    # DuckDuckGo HTML fallback
    if not rows:
        for block in re.findall(r'<div[^>]+class="result".*?</div>\s*</div>', html_text, flags=re.S|re.I):
            m=re.search(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',block,re.S|re.I)
            if not m: continue
            url=html.unescape(m.group(1)); title=clean_text(re.sub(r'<.*?>',' ',m.group(2)))
            if url.startswith('http'): rows.append({"url":url,"title":title,"snippet":""})
    return rows


def _bing_search(query, count=10, offset=0):
    """Best-effort public web discovery using HTML search pages; no marketplace API required."""
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"}
    errors=[]
    engines=[
        ("https://www.bing.com/search", {"q":query,"count":min(count,50),"first":offset+1,"setlang":"en"}),
        ("https://html.duckduckgo.com/html/", {"q":query,"s":offset}),
    ]
    for url,params in engines:
        try:
            r=requests.get(url,params=params,headers=headers,timeout=12)
            r.raise_for_status()
            rows=_parse_search_html(r.text)
            if rows: return rows[:count]
        except Exception as e:
            errors.append(type(e).__name__)
    raise RuntimeError("; ".join(errors) if errors else "No public search results")


def _product_page_metadata(url):
    """Extract public OpenGraph/JSON-LD product data. No login/API is required."""
    try:
        r=requests.get(url,headers={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140 Safari/537.36"},timeout=12,allow_redirects=True)
        if r.status_code >= 400: return {}
        txt=r.text[:1500000]
        def meta(prop):
            patterns=[r'<meta[^>]+(?:property|name)=["\']'+re.escape(prop)+r'["\'][^>]+content=["\']([^"\']+)',r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']'+re.escape(prop)+r'["\']']
            for pat in patterns:
                m=re.search(pat,txt,re.I)
                if m:return html.unescape(m.group(1)).strip()
            return ""
        title=meta("og:title") or meta("twitter:title")
        image=meta("og:image") or meta("twitter:image")
        desc=meta("og:description") or meta("description")
        price=""; currency=""; availability=""; brand=""
        for block in re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',txt,re.I|re.S):
            try:
                data=json.loads(html.unescape(block.strip()))
            except Exception:
                continue
            objs=data if isinstance(data,list) else (data.get("@graph",[]) if isinstance(data,dict) and "@graph" in data else [data])
            for obj in objs:
                if not isinstance(obj,dict): continue
                typ=obj.get("@type","")
                types=typ if isinstance(typ,list) else [typ]
                if "Product" not in types and "ProductGroup" not in types: continue
                title=title or str(obj.get("name", ""))
                imgs=obj.get("image",[])
                if isinstance(imgs,str): imgs=[imgs]
                image=image or (imgs[0] if imgs else "")
                desc=desc or str(obj.get("description", ""))
                b=obj.get("brand")
                brand=(b.get("name") if isinstance(b,dict) else str(b or "")) or brand
                offer=obj.get("offers",{})
                if isinstance(offer,list): offer=offer[0] if offer else {}
                if isinstance(offer,dict):
                    price=price or str(offer.get("price",offer.get("lowPrice","")))
                    currency=currency or str(offer.get("priceCurrency",""))
                    availability=availability or str(offer.get("availability",""))
                break
        return {"title":clean_text(title),"image":image,"description":clean_text(desc),"price":price,"currency":currency,"availability":availability,"brand":clean_text(brand)}
    except Exception:
        return {}


def _source_name(url):
    host=urlparse(url).netloc.lower().replace("www.","")
    for name,domain in PRODUCT_SOURCE_DOMAINS.items():
        if host.endswith(domain): return name
    return host.split(".")[0].title() if host else "Public Web"


def global_product_discover(max_cards=500, queries_per_run=40, season="All Seasons"):
    """Discover real public product pages across many worldwide sources.
    Product duplicates are NOT merged. Only the exact same URL is removed.
    Uses a small parallel public-web search pass so the main page can populate automatically.
    """
    # One broad query per category gives the feed coverage without requiring a marketplace API.
    category_queries=[]
    for category, qs in QUERY_PACK.items():
        if qs:
            q=qs[0]
            if season and season != "All Seasons":
                q += " " + " ".join(SEASONAL_TERMS.get(season, []))
            category_queries.append((category,q))
    category_queries=category_queries[:max(1,min(len(category_queries),int(queries_per_run)))]

    # Additional source-targeted searches keep the feed from becoming Amazon-heavy.
    source_queries=[]
    source_targets=list(PRODUCT_SOURCE_DOMAINS.items())
    for source_name, domain in source_targets:
        source_queries.append((source_name, domain, "useful products gadgets tools"))

    search_jobs=[]
    for category,q in category_queries:
        search_jobs.append((category, None, q))
    # Add one targeted query per source, but keep the total search pass bounded.
    search_jobs.extend(source_queries[:max(0, min(len(source_queries), 20))])

    raw=[]
    failures=[]
    def run_job(job):
        category, source_name, q = job
        if source_name:
            domain=PRODUCT_SOURCE_DOMAINS.get(source_name, "")
            query=f"site:{domain} {q}"
        else:
            query=f"{q} buy product"
        return job, _bing_search(query, count=8)

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures=[pool.submit(run_job,j) for j in search_jobs]
        for fut in as_completed(futures):
            job=search_jobs[0]
            try:
                job, results=fut.result()
                category, source_name, _=job
                for result in results:
                    raw.append((category, source_name, result))
            except Exception as e:
                failures.append(str(e))

    # Exact URL duplicate only. Similar products remain separate cards.
    candidates=[]; seen_urls=set()
    for category, source_hint, result in raw:
        url=result.get("url", "")
        if not url.startswith("http") or url in seen_urls:
            continue
        host=urlparse(url).netloc.lower()
        if any(host.endswith(d) for d in PRODUCT_SOURCE_DOMAINS.values()):
            seen_urls.add(url)
            candidates.append((category, source_hint, result))
        elif source_hint is None:
            # Public brand/manufacturer/product pages are allowed in the global feed.
            if any(x in host for x in ["youtube.com","instagram.com","tiktok.com","pinterest.com","facebook.com","google.com","bing.com"]):
                continue
            seen_urls.add(url)
            candidates.append((category, source_hint, result))
        if len(candidates)>=max_cards*2:
            break

    def enrich(item):
        category, source_hint, result=item
        url=result.get("url","")
        meta=_product_page_metadata(url)
        name=clean_text(meta.get("title") or result.get("title") or "")
        if len(name)<5:
            return None
        desc=clean_text(meta.get("description") or result.get("snippet") or "")
        text=f"{name} {desc} {category}"
        cat=classify(text)
        detected_season=seasonal_tag(text)
        low=text.lower()
        usefulness=min(100,72 + (10 if any(k in low for k in ["useful","problem","solution","save time","save money"]) else 0))
        demo=min(100,72 + (12 if any(k in low for k in ["before after","easy","portable","tool","how to","demonstration"]) else 0))
        uniq=78
        opp=round(min(100,usefulness*.35+demo*.25+uniq*.25+10))
        source=_source_name(url) if not source_hint else (_source_name(url) if urlparse(url).netloc else source_hint)
        links=[[f"{source} (direct)",url]] + marketplace_links(name)
        # Keep link list unique while retaining every marketplace search destination.
        seen=set(); clean_links=[]
        for label,link in links:
            if link not in seen:
                seen.add(link); clean_links.append([label,link])
        return {"name":name[:120],"category":cat,"segment":"Other Unique & Useful","trend_status":"Other","opportunity_score":opp,"trend_score":0,"uniqueness_score":uniq,"usefulness_score":usefulness,"demo_score":demo,"saturation_score":0,"why_interesting":f"Public product page found on {source}."+(f" Brand: {meta['brand']}." if meta.get("brand") else ""),"image_url":meta.get("image") or "","youtube_url":f"https://www.youtube.com/results?search_query={quote_plus(name)}","instagram_url":f"https://www.instagram.com/explore/tags/{re.sub(r'[^a-z0-9]+','',name.lower())[:60]}/","product_links":clean_links,"channel":source,"source":source,"source_url":url,"views":0,"likes":0,"comments":0,"published_at":"","season":detected_season,"price":meta.get("price",""),"currency":meta.get("currency",""),"availability":meta.get("availability","")}

    rows=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures=[pool.submit(enrich,item) for item in candidates[:max_cards*2]]
        for fut in as_completed(futures):
            try:
                row=fut.result()
                if row: rows.append(row)
                if len(rows)>=max_cards: break
            except Exception:
                continue
    # Stable order for the UI; no name-based product deduplication.
    return pd.DataFrame(rows[:max_cards]), sorted(set(failures))


def public_product_search(query, max_cards=500, season="All Seasons"):
    """Search the public web directly for a user-entered product/problem, independent of YouTube APIs."""
    query=clean_text(query)
    if not query: return pd.DataFrame()
    queries=[query]
    if season and season != "All Seasons": queries.append(query+" "+" ".join(SEASONAL_TERMS.get(season, [])))
    jobs=[]
    for q in queries:
        jobs.append((None,q+" buy product"))
        for source,domain in list(PRODUCT_SOURCE_DOMAINS.items())[:16]:
            jobs.append((source,f"site:{domain} {q}"))
    raw=[]; failures=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        future_map={pool.submit(_bing_search,q,count=8):(source,q) for source,q in jobs}
        for fut,(source,q) in future_map.items():
            try:
                for result in fut.result(): raw.append((source,result))
            except Exception as e: failures.append(type(e).__name__)
    seen=set(); candidates=[]
    for source_hint,result in raw:
        url=result.get("url","")
        if not url.startswith("http") or url in seen: continue
        host=urlparse(url).netloc.lower()
        if any(host.endswith(d) for d in PRODUCT_SOURCE_DOMAINS.values()) or source_hint is None:
            if any(x in host for x in ["youtube.com","instagram.com","tiktok.com","pinterest.com","facebook.com","google.com","bing.com","duckduckgo.com"]): continue
            seen.add(url); candidates.append((source_hint,result))
        if len(candidates)>=max_cards*2: break
    rows=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        future_map={pool.submit(_product_page_metadata,item[1].get("url","")):item for item in candidates[:max_cards*2]}
        for fut,item in future_map.items():
            try:
                meta=fut.result(); result=item[1]
                name=clean_text(meta.get("title") or result.get("title") or "")
                if len(name)<5: continue
                desc=clean_text(meta.get("description") or result.get("snippet") or "")
                text=f"{name} {desc} {query}"
                cat=classify(text); detected=seasonal_tag(text)
                low=text.lower(); usefulness=min(100,72+(10 if any(k in low for k in ["useful","problem","solution","save time","save money"]) else 0)); demo=min(100,72+(12 if any(k in low for k in ["before after","easy","portable","tool","how to","demonstration"]) else 0)); uniq=78
                opp=round(min(100,usefulness*.35+demo*.25+uniq*.25+10))
                source=_source_name(result.get("url",""))
                links=[[f"{source} (direct)",result.get("url","")]]+marketplace_links(name)
                unique_links=[]; seen_links=set()
                for label,link in links:
                    if link and link not in seen_links: seen_links.add(link); unique_links.append([label,link])
                rows.append({"name":name[:120],"category":cat,"segment":"Other Unique & Useful","trend_status":"Other","opportunity_score":opp,"trend_score":0,"uniqueness_score":uniq,"usefulness_score":usefulness,"demo_score":demo,"saturation_score":0,"why_interesting":f"Public product page found on {source}.","image_url":meta.get("image") or "","youtube_url":f"https://www.youtube.com/results?search_query={quote_plus(name)}","instagram_url":f"https://www.instagram.com/explore/tags/{re.sub(r'[^a-z0-9]+','',name.lower())[:60]}/","product_links":unique_links,"channel":source,"source":source,"source_url":result.get("url",""),"views":0,"likes":0,"comments":0,"published_at":"","season":detected,"price":meta.get("price",""),"currency":meta.get("currency",""),"availability":meta.get("availability","")})
            except Exception: continue
            if len(rows)>=max_cards: break
    return pd.DataFrame(rows[:max_cards])

st.session_state.setdefault("live_df", pd.DataFrame())
st.session_state.setdefault("global_products_df", pd.DataFrame())
st.session_state.setdefault("search_df", pd.DataFrame())
st.session_state.setdefault("search_term", "")
st.session_state.setdefault("favorites", [])
st.session_state.setdefault("last_error", "")
st.session_state.setdefault("page", 1)
st.session_state.setdefault("view", "all")
st.session_state.setdefault("youtube_trends_df", pd.DataFrame())
st.session_state.setdefault("instagram_trends_df", pd.DataFrame())
st.session_state.setdefault("trending_stars_df", pd.DataFrame())
st.session_state.setdefault("season_filter", "All Seasons")
st.session_state.setdefault("auto_loaded", False)
st.session_state.setdefault("discovery_running", False)

st.markdown("""<style>
.block-container{max-width:1450px;padding:1rem 2rem 3rem}.hero{padding:24px;border:1px solid #e6e6e6;border-radius:22px;background:linear-gradient(135deg,#f7f9ff,#fff);margin-bottom:18px}.hero h1{margin:0;font-size:2.1rem;font-weight:850}.hero p{margin:5px 0 0;color:#666}.card{border:1px solid #e4e4e4;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.05);height:100%}.card-title{font-size:1.05rem;font-weight:800;line-height:1.3;margin:10px 0 6px}.badge{display:inline-block;font-size:11px;font-weight:750;padding:5px 8px;border-radius:999px;background:#f1f3f5;margin:0 5px 5px 0}.hot{background:#fff0ed;color:#c0392b}.rise{background:#fff7dc;color:#9a6900}.why{font-size:13px;color:#555;line-height:1.45;min-height:48px}.score{font-size:1.35rem;font-weight:850}.muted{color:#777;font-size:12px}.buttonrow{display:flex;gap:8px;margin-top:12px}.pagebar{padding:12px 14px;border:1px solid #e7e7e7;border-radius:14px;background:#fff;margin:12px 0}.small{font-size:12px;color:#777}.trend-star-note{font-size:12px;color:#666;margin:6px 0 14px}@media(max-width:700px){.block-container{padding:.7rem}.hero h1{font-size:1.65rem}.buttonrow{display:block}.buttonrow>*{margin-bottom:6px;width:100%}}
</style>""",unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Discovery settings")
    api_key=st.text_input("YouTube API key",type="password",value=st.secrets.get("YOUTUBE_API_KEY",os.getenv("YOUTUBE_API_KEY","")) if hasattr(st,"secrets") else os.getenv("YOUTUBE_API_KEY",""))
    region=st.selectbox("Region",["IN","US","GB","AE","AU","CA","SG","JP"],index=0)
    lookback=st.slider("Lookback days",1,90,30)
    per_query=st.slider("Videos per search",5,50,20)
    max_queries=st.slider("Search queries",5,30,20)
    if st.button("🌍 Refresh Global Products",use_container_width=True):
        with st.spinner("Discovering product pages across the public web…"):
            try:
                found, failed_sources=global_product_discover(MAX_CARDS, max_queries, st.session_state.get("season_filter","All Seasons"))
                st.session_state.global_products_df=found
                st.session_state.live_df=found.copy()
                st.session_state.view="all"; st.session_state.page=1; st.session_state.last_error=(f"No public product results were returned. Sources unavailable: {", ".join(failed_sources)}" if found.empty and failed_sources else "")
            except Exception as e:
                st.session_state.last_error=f"Global discovery failed: {type(e).__name__}: {e}"
    st.caption("Main feed uses public-web product discovery. YouTube API is optional enrichment, not a requirement for the main catalog.")

# Automatically populate the main page on first load. No demo catalog is used as the default feed.
if not st.session_state.auto_loaded and st.session_state.global_products_df.empty:
    st.session_state.auto_loaded = True
    with st.spinner("Loading global products from public product sources…"):
        try:
            found, failed_sources = global_product_discover(MAX_CARDS, 19, st.session_state.get("season_filter", "All Seasons"))
            st.session_state.global_products_df = found
            st.session_state.live_df = found.copy()
            st.session_state.page = 1
            if found.empty:
                st.session_state.last_error = "No live public product pages were retrieved. Use Refresh Global Products to try again."
            else:
                st.session_state.last_error = ""
        except Exception as e:
            st.session_state.last_error = f"Automatic global discovery failed: {type(e).__name__}: {e}"

st.markdown('<div class="hero"><h1>🔎 Product Hunter</h1><p>Global product discovery across categories and public product sources. Trend signals are connected separately through Trending Stars. Product duplicates are not merged.</p></div>',unsafe_allow_html=True)

raw=st.session_state.global_products_df.copy() if not st.session_state.global_products_df.empty else st.session_state.live_df.copy()

# Search and trend controls stay together in one row for quick product discovery.
search_col, search_btn_col, stars_col, fav_col = st.columns([4.9,1.0,1.8,1.25])
with search_col:
    search_term=st.text_input("Search products",placeholder="Search products, problems or gadgets…",label_visibility="collapsed",key="search_input")
with search_btn_col:
    do_search=st.button("🔎 Search",use_container_width=True)
with stars_col:
    trending_stars=st.button("⭐ Trending Stars",use_container_width=True)
with fav_col:
    show_fav=st.button(f"♥ Favorites ({len(st.session_state.favorites)})",use_container_width=True)

if trending_stars:
    st.session_state.view="trending_stars"; st.session_state.page=1
    # The button is a unified trend hub. API-backed sources are optional; public trend links remain usable without API keys.
    source=st.session_state.get("youtube_trends_df",pd.DataFrame())
    st.session_state.trending_stars_df=source.copy()
    st.session_state.last_error=""

if do_search:
    if not search_term.strip():
        st.warning("Enter a product or problem to search.")
    else:
        # Product search is always source-agnostic. YouTube API data belongs to Trending Stars, not the main product feed.
        with st.spinner(f"Searching public product sources for: {search_term.strip()} …"):
            try:
                st.session_state.search_df=public_product_search(search_term.strip(), MAX_CARDS, st.session_state.get("season_filter","All Seasons"))
                st.session_state.search_term=search_term.strip(); st.session_state.page=1; st.session_state.last_error=""
            except Exception as e:
                st.session_state.last_error=f"Public-web product search failed: {type(e).__name__}: {e}"

if show_fav:
    st.session_state.page=1

if st.session_state.last_error: st.warning(st.session_state.last_error)

if st.session_state.view=="trending_stars":
    st.subheader("⭐ Trending Stars")
    st.caption("One hub for the available trend sources. These links open the source directly; API access is optional and source availability varies by platform.")
    trend_cols=st.columns(6)
    trend_links=[("YouTube","https://www.youtube.com/results?search_query=trending+products"),("Instagram","https://www.instagram.com/explore/tags/viralproducts/"),("TikTok","https://www.tiktok.com/tag/viralproducts"),("Pinterest","https://www.pinterest.com/search/pins/?q=trending%20products"),("Google Trends","https://trends.google.com/trending?geo=US"),("Public Web","https://www.google.com/search?q=trending+products")]
    for c,(label,url) in zip(trend_cols,trend_links):
        with c: st.link_button(label,url,use_container_width=True)
    data=st.session_state.get("trending_stars_df",pd.DataFrame()).copy() if not st.session_state.get("trending_stars_df",pd.DataFrame()).empty else pd.DataFrame()
elif show_fav:
    data=pd.DataFrame(st.session_state.favorites) if st.session_state.favorites else pd.DataFrame()
elif not st.session_state.search_df.empty:
    data=st.session_state.search_df.copy()
elif st.session_state.search_term:
    data=pd.DataFrame()
else:
    data=raw.copy()

# Filters apply only after an explicit search or while browsing the default feed.
c1,c2,c3,c4=st.columns([2.4,2.0,2.0,2.0])
with c1: season=st.selectbox("Season",["All Seasons"]+list(SEASONAL_TERMS.keys()),label_visibility="collapsed",key="season_filter")
with c2: cat=st.selectbox("Category",["All"]+sorted(data.category.dropna().unique().tolist()) if not data.empty else ["All"],label_visibility="collapsed")
with c3: status=st.selectbox("Trend",["All","Viral/Trending","Rising","Other"],label_visibility="collapsed")
with c4: sort=st.selectbox("Sort",["Opportunity","Newest","Trend","Views","Usefulness"],label_visibility="collapsed")

if not data.empty:
    if season!="All Seasons":
        data=data[data["season"].fillna("").astype(str).str.contains(season, case=False, na=False)] if "season" in data.columns else data.iloc[0:0]
    if cat!="All": data=data[data.category==cat]
    if status!="All": data=data[data.trend_status==status]
    if sort=="Newest": data["_date"]=pd.to_datetime(data.get("published_at"),errors="coerce",utc=True); data=data.sort_values("_date",ascending=False)
    elif sort=="Views": data=data.sort_values("views",ascending=False)
    elif sort=="Trend": data=data.sort_values("trend_score",ascending=False)
    elif sort=="Usefulness": data=data.sort_values("usefulness_score",ascending=False)
    else: data=data.sort_values("opportunity_score",ascending=False)
    data=data.head(MAX_CARDS).reset_index(drop=True)

page=st.session_state.page
start=(page-1)*PAGE_SIZE; page_data=data.iloc[start:start+PAGE_SIZE] if not data.empty else data

if len(page_data)==0:
    st.info("No cards on this page yet. Run live discovery or change the filters.")
else:
    for i in range(0,len(page_data),3):
        cols=st.columns(3,gap="medium")
        for j,col in enumerate(cols):
            if i+j>=len(page_data): continue
            p=page_data.iloc[i+j]
            with col:
                with st.container(border=True):
                    img=str(p.get("image_url","") or "")
                    if img.startswith("asset:"): img=str(ASSET_DIR/img.split(":",1)[1])
                    if not img or img=="nan":
                        st.markdown('<div style="height:210px;border-radius:14px;background:#f3f5f8;display:flex;align-items:center;justify-content:center;color:#7a7f87;font-size:14px;">Product image not available</div>', unsafe_allow_html=True)
                    else:
                        st.image(img,use_container_width=True)
                    stat=str(p.get("trend_status","Other")); cls="hot" if stat=="Viral/Trending" else ("rise" if stat=="Rising" else "")
                    badges=f'<span class="badge {cls}">{html.escape(stat)}</span><span class="badge">{html.escape(str(p.get("category","")))}</span>'
                    if p.get("season"): badges+=f'<span class="badge">🌦️ {html.escape(str(p.get("season")))}</span>'
                    st.markdown(badges,unsafe_allow_html=True)
                    st.markdown(f'<div class="card-title">{html.escape(str(p.get("name","Unknown product")))}</div>',unsafe_allow_html=True)
                    if str(p.get("price", "")) not in ("", "nan"):
                        st.markdown(f"**Price:** {html.escape(str(p.get("currency","")))} {html.escape(str(p.get("price","")))}")
                    st.markdown(f'<div class="muted">{html.escape(str(p.get("channel",p.get("source",""))))} • {int(p.get("views",0)):,} views</div>',unsafe_allow_html=True)
                    st.write(str(p.get("why_interesting","")))
                    st.markdown(f'<div class="score">{int(p.get("opportunity_score",0))}<span class="muted"> / 100 opportunity</span></div>',unsafe_allow_html=True)
                    st.caption(f"Trend {int(p.get('trend_score',0))} • Usefulness {int(p.get('usefulness_score',0))} • Uniqueness {int(p.get('uniqueness_score',0))}")
                    fav_key=normalize_product_name(str(p.get("name","")))+"|"+str(p.get("youtube_url",""))
                    is_fav=any(normalize_product_name(str(f.get("name","")))+"|"+str(f.get("youtube_url",""))==fav_key for f in st.session_state.favorites)
                    fcol,b1,b2=st.columns([.8,1.6,1.6])
                    with fcol:
                        if st.button("♥" if is_fav else "♡",key=f"fav_{page}_{i}_{j}",help="Save for future reference"):
                            if is_fav:
                                st.session_state.favorites=[f for f in st.session_state.favorites if normalize_product_name(str(f.get("name","")))+"|"+str(f.get("youtube_url",""))!=fav_key]
                            else:
                                st.session_state.favorites.append(p.to_dict())
                            st.rerun()
                    with b1: st.link_button("▶ YouTube",str(p.get("youtube_url","")),use_container_width=True)
                    with b2: st.link_button("◎ Instagram",str(p.get("instagram_url","")),use_container_width=True)
                    links=p.get("product_links",[]) or []
                    with st.popover(f"🛒 Product links ({len(links)})",use_container_width=True):
                        st.caption("All product URLs currently available for this card. Search links are only used when no direct URL was found.")
                        for label,url in links:
                            st.link_button(label,url,use_container_width=True)

# Compact, centered page numbers below the cards.
st.markdown('<div class="bottom-pages">',unsafe_allow_html=True)
left, b1, b2, b3, b4, b5, right = st.columns([5, 0.65, 0.65, 0.65, 0.65, 0.65, 5])
for n, bc in enumerate([b1, b2, b3, b4, b5], 1):
    with bc:
        if st.button(str(n), key=f"bottom_page_{n}", use_container_width=True):
            st.session_state.page=n
            st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

st.divider()
st.caption("Pages 1–5 contain up to 100 cards each. Main feed is source-agnostic; product duplicates are not merged. ⭐ Trending Stars is the unified hub for YouTube, Instagram, TikTok, Pinterest, Google Trends and public-web trend signals. Season is a primary filter.")
