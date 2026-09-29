import os, re, math, html
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse
from pathlib import Path
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Product Hunter", page_icon="🔎", layout="wide", initial_sidebar_state="collapsed")

PAGE_SIZE = 100
TOTAL_PAGES = 5
MAX_CARDS = PAGE_SIZE * TOTAL_PAGES
ASSET_DIR = Path(__file__).parent / "assets"

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

DEMO = [
 {"name":"Foldable Food Sealer","category":"Home & Kitchen","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":86,"trend_score":72,"uniqueness_score":88,"usefulness_score":91,"demo_score":90,"saturation_score":38,"why_interesting":"Easy before/after demonstration and solves a common food-storage problem.","image_url":"asset:sealer.jpg","youtube_url":"https://www.youtube.com/results?search_query=mini+food+bag+sealer","instagram_url":"https://www.instagram.com/explore/tags/foodsealer/","product_links":[["Amazon India","https://www.amazon.in/s?k=mini+food+bag+sealer"],["Flipkart","https://www.flipkart.com/search?q=mini%20food%20bag%20sealer"],["Meesho","https://www.meesho.com/search?q=mini%20food%20bag%20sealer"]]},
 {"name":"Smart Soil Moisture Meter","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":84,"trend_score":68,"uniqueness_score":84,"usefulness_score":92,"demo_score":86,"saturation_score":34,"why_interesting":"Useful for home gardening and farming; readings are easy to demonstrate on video.","image_url":"asset:soil.jpg","youtube_url":"https://www.youtube.com/results?search_query=soil+moisture+meter","instagram_url":"https://www.instagram.com/explore/tags/soilmoisture/","product_links":[["Amazon India","https://www.amazon.in/s?k=soil+moisture+meter"],["Flipkart","https://www.flipkart.com/search?q=soil%20moisture%20meter"],["Meesho","https://www.meesho.com/search?q=soil%20moisture%20meter"]]},
 {"name":"Portable Tyre Inflator","category":"Car & Bike","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":79,"trend_score":91,"uniqueness_score":63,"usefulness_score":94,"demo_score":95,"saturation_score":71,"why_interesting":"Strong visual demonstration and clear emergency-use case.","image_url":"asset:inflator.jpg","youtube_url":"https://www.youtube.com/results?search_query=portable+tyre+inflator","instagram_url":"https://www.instagram.com/explore/tags/portabletyreinflator/","product_links":[["Amazon India","https://www.amazon.in/s?k=portable+tyre+inflator"],["Flipkart","https://www.flipkart.com/search?q=portable%20tyre%20inflator"],["Meesho","https://www.meesho.com/search?q=portable%20tyre%20inflator"]]},
 {"name":"Rechargeable Mini Chopper","category":"Home & Kitchen","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":76,"trend_score":94,"uniqueness_score":61,"usefulness_score":89,"demo_score":96,"saturation_score":82,"why_interesting":"Highly demonstrable product, but social content is already crowded.","image_url":"asset:chopper.jpg","youtube_url":"https://www.youtube.com/results?search_query=rechargeable+mini+chopper","instagram_url":"https://www.instagram.com/explore/tags/minichopper/","product_links":[["Amazon India","https://www.amazon.in/s?k=rechargeable+mini+chopper"],["Flipkart","https://www.flipkart.com/search?q=rechargeable%20mini%20chopper"],["Meesho","https://www.meesho.com/search?q=rechargeable%20mini%20chopper"]]},
 {"name":"Hand Weeder Tool","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Other","opportunity_score":73,"trend_score":48,"uniqueness_score":87,"usefulness_score":88,"demo_score":84,"saturation_score":22,"why_interesting":"Less saturated and particularly relevant for garden and small-farm users.","image_url":"asset:weeder.jpg","youtube_url":"https://www.youtube.com/results?search_query=hand+weeder+tool","instagram_url":"https://www.instagram.com/explore/tags/handweeder/","product_links":[["Amazon India","https://www.amazon.in/s?k=hand+weeder+tool"],["Flipkart","https://www.flipkart.com/search?q=hand%20weeder%20tool"],["Meesho","https://www.meesho.com/search?q=hand%20weeder%20tool"]]},
 {"name":"Travel Cable Organizer","category":"Travel","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":81,"trend_score":70,"uniqueness_score":78,"usefulness_score":87,"demo_score":82,"saturation_score":42,"why_interesting":"Compact travel problem-solver with an easy visual transformation demo.","image_url":"asset:travel.jpg","youtube_url":"https://www.youtube.com/results?search_query=travel+cable+organizer","instagram_url":"https://www.instagram.com/explore/tags/travelcableorganizer/","product_links":[["Amazon India","https://www.amazon.in/s?k=travel+cable+organizer"],["Flipkart","https://www.flipkart.com/search?q=travel%20cable%20organizer"],["Meesho","https://www.meesho.com/search?q=travel%20cable%20organizer"]]},
]


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
        ["Flipkart",f"https://www.flipkart.com/search?q={quote_plus(name)}"],
        ["Meesho",f"https://www.meesho.com/search?q={q}"],
        ["eBay",f"https://www.ebay.com/sch/i.html?_nkw={q}"],
        ["AliExpress",f"https://www.aliexpress.com/w/wholesale-{q}.html"],
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

def dedupe_products(df):
    if df.empty: return df
    x=df.copy(); x["_product_key"]=x["name"].map(normalize_product_name)
    x=x.sort_values(["opportunity_score","views"],ascending=False)
    x=x.drop_duplicates("_product_key",keep="first").drop(columns=["_product_key"],errors="ignore")
    return x.reset_index(drop=True)

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


st.session_state.setdefault("live_df", pd.DataFrame())
st.session_state.setdefault("search_df", pd.DataFrame())
st.session_state.setdefault("search_term", "")
st.session_state.setdefault("favorites", [])
st.session_state.setdefault("last_error", "")
st.session_state.setdefault("page", 1)
st.session_state.setdefault("view", "all")
st.session_state.setdefault("youtube_trends_df", pd.DataFrame())
st.session_state.setdefault("instagram_trends_df", pd.DataFrame())

st.markdown("""<style>
.block-container{max-width:1450px;padding:1rem 2rem 3rem}.hero{padding:24px;border:1px solid #e6e6e6;border-radius:22px;background:linear-gradient(135deg,#f7f9ff,#fff);margin-bottom:18px}.hero h1{margin:0;font-size:2.1rem;font-weight:850}.hero p{margin:5px 0 0;color:#666}.card{border:1px solid #e4e4e4;border-radius:18px;overflow:hidden;background:#fff;box-shadow:0 2px 12px rgba(0,0,0,.05);height:100%}.card-title{font-size:1.05rem;font-weight:800;line-height:1.3;margin:10px 0 6px}.badge{display:inline-block;font-size:11px;font-weight:750;padding:5px 8px;border-radius:999px;background:#f1f3f5;margin:0 5px 5px 0}.hot{background:#fff0ed;color:#c0392b}.rise{background:#fff7dc;color:#9a6900}.why{font-size:13px;color:#555;line-height:1.45;min-height:48px}.score{font-size:1.35rem;font-weight:850}.muted{color:#777;font-size:12px}.buttonrow{display:flex;gap:8px;margin-top:12px}.pagebar{padding:12px 14px;border:1px solid #e7e7e7;border-radius:14px;background:#fff;margin:12px 0}.small{font-size:12px;color:#777}@media(max-width:700px){.block-container{padding:.7rem}.hero h1{font-size:1.65rem}.buttonrow{display:block}.buttonrow>*{margin-bottom:6px;width:100%}}
</style>""",unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Discovery settings")
    api_key=st.text_input("YouTube API key",type="password",value=st.secrets.get("YOUTUBE_API_KEY",os.getenv("YOUTUBE_API_KEY","")) if hasattr(st,"secrets") else os.getenv("YOUTUBE_API_KEY",""))
    region=st.selectbox("Region",["IN","US","GB","AE","AU","CA","SG","JP"],index=0)
    lookback=st.slider("Lookback days",1,90,30)
    per_query=st.slider("Videos per search",5,50,20)
    max_queries=st.slider("Search queries",5,30,20)
    if st.button("🚀 Run discovery",use_container_width=True):
        if not api_key: st.session_state.last_error="Add your YouTube Data API v3 key first."
        else:
            with st.spinner("Collecting individual video references…"):
                try:
                    st.session_state.live_df=youtube_discover(api_key,region,lookback,per_query,max_queries); st.session_state.last_error=""
                except Exception as e: st.session_state.last_error=f"Discovery failed: {type(e).__name__}: {e}"

st.markdown('<div class="hero"><h1>🔎 Product Hunter</h1><p>Browse individual product-reference videos and compare products yourself. Product duplicates are not filtered.</p></div>',unsafe_allow_html=True)

raw=st.session_state.live_df.copy() if not st.session_state.live_df.empty else pd.DataFrame(DEMO)

# Search and trend controls stay together in one row for quick product discovery.
search_col, search_btn_col, yt_col, ig_col, fav_col = st.columns([4.6,1.0,1.25,1.25,1.25])
with search_col:
    search_term=st.text_input("Search products",placeholder="Search products, problems or gadgets…",label_visibility="collapsed",key="search_input")
with search_btn_col:
    do_search=st.button("🔎 Search",use_container_width=True)
with yt_col:
    yt_trends=st.button("▶ YouTube Trends",use_container_width=True)
with ig_col:
    ig_trends=st.button("◎ Instagram Trends",use_container_width=True)
with fav_col:
    show_fav=st.button(f"♥ Favorites ({len(st.session_state.favorites)})",use_container_width=True)

if yt_trends:
    st.session_state.view="youtube_trends"; st.session_state.page=1
    if not api_key:
        st.session_state.last_error="Add your YouTube API key in Settings to fetch live YouTube trends."
    else:
        with st.spinner("Fetching current product trend videos…"):
            try:
                st.session_state.youtube_trends_df=youtube_trends(api_key,region,100); st.session_state.last_error=""
            except Exception as e: st.session_state.last_error=f"YouTube Trends failed: {type(e).__name__}: {e}"

if ig_trends:
    st.session_state.view="instagram_trends"; st.session_state.page=1
    source=st.session_state.get("youtube_trends_df",pd.DataFrame())
    if source.empty: source=st.session_state.get("live_df",pd.DataFrame())
    if source.empty: source=pd.DataFrame(DEMO)
    st.session_state.instagram_trends_df=instagram_trend_references(source); st.session_state.last_error=""

if do_search:
    if not search_term.strip():
        st.warning("Enter a product or problem to search.")
    elif not api_key:
        st.session_state.search_df=raw.copy()
        st.session_state.search_term=search_term.strip()
        st.session_state.last_error="Demo mode: add a YouTube API key in Settings for live video search."
    else:
        with st.spinner(f"Searching all matching videos for: {search_term.strip()} …"):
            try:
                st.session_state.search_df=youtube_search_unique(api_key,search_term,region,100)
                st.session_state.search_term=search_term.strip(); st.session_state.last_error=""; st.session_state.page=1
            except Exception as e:
                st.session_state.last_error=f"Search failed: {type(e).__name__}: {e}"

if show_fav:
    st.session_state.page=1

if st.session_state.last_error: st.warning(st.session_state.last_error)

if st.session_state.view=="youtube_trends":
    data=st.session_state.get("youtube_trends_df",pd.DataFrame()).copy() if not st.session_state.get("youtube_trends_df",pd.DataFrame()).empty else pd.DataFrame()
elif st.session_state.view=="instagram_trends":
    data=st.session_state.get("instagram_trends_df",pd.DataFrame()).copy() if not st.session_state.get("instagram_trends_df",pd.DataFrame()).empty else pd.DataFrame()
elif show_fav:
    data=pd.DataFrame(st.session_state.favorites) if st.session_state.favorites else pd.DataFrame()
elif not st.session_state.search_df.empty:
    data=st.session_state.search_df.copy()
elif st.session_state.search_term:
    data=pd.DataFrame()
else:
    data=raw.copy()

# Filters apply only after an explicit search or while browsing the default feed.
c1,c2,c3=st.columns([2,2,2])
with c1: cat=st.selectbox("Category",["All"]+sorted(data.category.dropna().unique().tolist()) if not data.empty else ["All"],label_visibility="collapsed")
with c2: status=st.selectbox("Trend",["All","Viral/Trending","Rising","Other"],label_visibility="collapsed")
with c3: sort=st.selectbox("Sort",["Opportunity","Newest","Trend","Views","Usefulness"],label_visibility="collapsed")

if not data.empty:
    if cat!="All": data=data[data.category==cat]
    if status!="All": data=data[data.trend_status==status]
    if sort=="Newest": data["_date"]=pd.to_datetime(data.get("published_at"),errors="coerce",utc=True); data=data.sort_values("_date",ascending=False)
    elif sort=="Views": data=data.sort_values("views",ascending=False)
    elif sort=="Trend": data=data.sort_values("trend_score",ascending=False)
    elif sort=="Usefulness": data=data.sort_values("usefulness_score",ascending=False)
    else: data=data.sort_values("opportunity_score",ascending=False)
    data=data.head(MAX_CARDS).reset_index(drop=True)

# Simple page navigation: five separate page buttons, no page/card metrics.
pcols=st.columns(5)
for n,pc in enumerate(pcols,1):
    with pc:
        if st.button(str(n),key=f"page_{n}",use_container_width=True): st.session_state.page=n
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
                    if not img or img=="nan": img=str(ASSET_DIR/"product-fallback.jpg")
                    st.image(img,use_container_width=True)
                    stat=str(p.get("trend_status","Other")); cls="hot" if stat=="Viral/Trending" else ("rise" if stat=="Rising" else "")
                    badges=f'<span class="badge {cls}">{html.escape(stat)}</span><span class="badge">{html.escape(str(p.get("category","")))}</span>'
                    if p.get("season"): badges+=f'<span class="badge">🌦️ {html.escape(str(p.get("season")))}</span>'
                    st.markdown(badges,unsafe_allow_html=True)
                    st.markdown(f'<div class="card-title">{html.escape(str(p.get("name","Unknown product")))}</div>',unsafe_allow_html=True)
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

# Small page numbers below the cards as requested.
st.markdown('<div class="bottom-pages">',unsafe_allow_html=True)
bcols=st.columns(5)
for n,bc in enumerate(bcols,1):
    with bc:
        if st.button(str(n),key=f"bottom_page_{n}",use_container_width=True): st.session_state.page=n; st.rerun()
st.markdown('</div>',unsafe_allow_html=True)

st.divider()
st.caption("Pages 1–5 contain up to 100 cards each. Discovery and Search keep individual videos; repeated products are not merged. Trend pages keep individual references.")
