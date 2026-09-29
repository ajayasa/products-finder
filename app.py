import os, re, math, html
from datetime import datetime, timedelta, timezone
from urllib.parse import quote_plus, urlparse
import requests
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Global Product Hunter", page_icon="🔎", layout="wide", initial_sidebar_state="expanded")

CATEGORIES = [
    "Unique & Clever", "Problem-Solving", "Home & Kitchen", "Tech & Gadgets", "Car & Bike",
    "Travel", "Personal Use & Grooming", "Village / Rural", "Farming & Agriculture", "Seasonal",
    "Outdoor & Garden", "Tools & DIY", "Cleaning & Organization", "Safety & Emergency",
    "Kids & Parents", "Elderly / Senior-Friendly", "Office & Work From Home", "Money-Saving", "Local / Indian-Specific"
]
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
    "Travel Season": ["travel", "holiday", "vacation", "trip", "airport"]
}
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
    "Local / Indian-Specific": ["Indian household useful products", "Indian kitchen gadgets", "Indian daily use products"]
}

DEMO = [
 {"name":"Foldable Food Sealer","category":"Home & Kitchen","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":86,"trend_score":72,"uniqueness_score":88,"usefulness_score":91,"demo_score":90,"saturation_score":38,"why_interesting":"Easy before/after demonstration and solves a common food-storage problem.","product_url":"https://www.amazon.in/s?k=mini+food+bag+sealer","reference_url":"https://www.youtube.com/results?search_query=mini+food+bag+sealer","image_url":"","source":"Demo"},
 {"name":"Smart Soil Moisture Meter","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":84,"trend_score":68,"uniqueness_score":84,"usefulness_score":92,"demo_score":86,"saturation_score":34,"why_interesting":"Useful for home gardening and farming; readings are easy to demonstrate on video.","product_url":"https://www.amazon.in/s?k=soil+moisture+meter","reference_url":"https://www.youtube.com/results?search_query=soil+moisture+meter","image_url":"","source":"Demo"},
 {"name":"Portable Tyre Inflator","category":"Car & Bike","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":79,"trend_score":91,"uniqueness_score":63,"usefulness_score":94,"demo_score":95,"saturation_score":71,"why_interesting":"Strong visual demonstration and clear emergency-use case.","product_url":"https://www.amazon.in/s?k=portable+tyre+inflator","reference_url":"https://www.youtube.com/results?search_query=portable+tyre+inflator","image_url":"","source":"Demo"},
 {"name":"Rechargeable Mini Chopper","category":"Home & Kitchen","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":76,"trend_score":94,"uniqueness_score":61,"usefulness_score":89,"demo_score":96,"saturation_score":82,"why_interesting":"Highly demonstrable product, but social content is already crowded.","product_url":"https://www.amazon.in/s?k=rechargeable+mini+chopper","reference_url":"https://www.youtube.com/results?search_query=rechargeable+mini+chopper","image_url":"","source":"Demo"},
 {"name":"Hand Weeder Tool","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Other","opportunity_score":73,"trend_score":48,"uniqueness_score":87,"usefulness_score":88,"demo_score":84,"saturation_score":22,"why_interesting":"Less saturated and particularly relevant for garden and small-farm users.","product_url":"https://www.amazon.in/s?k=hand+weeder+tool","reference_url":"https://www.youtube.com/results?search_query=hand+weeder+tool","image_url":"","source":"Demo"},
 {"name":"Travel Cable Organizer","category":"Travel","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":81,"trend_score":70,"uniqueness_score":78,"usefulness_score":87,"demo_score":82,"saturation_score":42,"why_interesting":"Compact travel problem-solver with an easy visual transformation demo.","product_url":"https://www.amazon.in/s?k=travel+cable+organizer","reference_url":"https://www.youtube.com/results?search_query=travel+cable+organizer","image_url":"","source":"Demo"},
]

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
 "Unique & Clever":"clever innovative invention unusual unique smart"
}

def clean_text(x):
    return re.sub(r"\s+", " ", html.unescape(str(x or ""))).strip()

def classify(text):
    t=clean_text(text).lower()
    scores=[]
    for cat, words in KEYWORDS.items():
        hits=sum(1 for w in words.split() if w in t)
        scores.append((hits,cat))
    best=max(scores)
    cat=best[1] if best[0]>0 else "Unique & Clever"
    return cat

def seasonal_tag(text):
    t=clean_text(text).lower()
    hits=[]
    for season, words in SEASONAL_TERMS.items():
        if any(w in t for w in words): hits.append(season)
    return ", ".join(hits)

def extract_urls(text):
    urls=re.findall(r"https?://[^\s<>\]\)\"']+", text or "")
    out=[]
    for u in urls:
        u=u.rstrip(".,;!?)]}")
        host=urlparse(u).netloc.lower()
        if host and not any(x in host for x in ["youtube.com","youtu.be","instagram.com","facebook.com"]): out.append(u)
    return out

def candidate_name(title):
    t=clean_text(title)
    t=re.sub(r"\b(amazon|review|unboxing|testing|test|viral|must have|best|top|new|cool|useful|gadget|gadgets|product|products)\b", " ", t, flags=re.I)
    t=re.sub(r"[|•:]+", " ", t)
    t=re.sub(r"\([^)]*\)|\[[^]]*\]", " ", t)
    t=re.sub(r"\s+[-–—]\s+.*$", "", t)
    t=clean_text(t)
    if len(t)<5: t=clean_text(title)
    return t[:90]

def scores_for(v, source_count=1, creator_count=1):
    views=max(int(v.get("views",0)),0); likes=max(int(v.get("likes",0)),0); comments=max(int(v.get("comments",0)),0)
    age=max(float(v.get("age_days",1)),0.25)
    velocity=math.log10(views+1)/math.log10(age+2)*18
    engagement=((likes+comments*3)/(views+1))*100
    trend=max(0,min(100,round(velocity*3.0 + min(engagement*2.5,25) + min(source_count*4,20))))
    usefulness=80
    demo=82
    title=clean_text(v.get("title","")).lower()
    if any(w in title for w in ["how", "test", "testing", "before after", "hack", "demo"]): demo+=8
    if any(w in title for w in ["useful", "problem", "solution", "life changing"]): usefulness+=8
    uniqueness=82 if source_count<=2 else max(45,82-source_count*5)
    saturation=max(10,min(95,round(source_count*9 + creator_count*4)))
    opportunity=round(max(0,min(100,trend*0.30+uniqueness*0.22+usefulness*0.22+demo*0.16+(100-saturation)*0.10)))
    if trend>=78 and saturation>=65: status="Viral/Trending"
    elif trend>=55: status="Rising"
    else: status="Other"
    return trend,uniqueness,usefulness,demo,saturation,opportunity,status

def youtube_discover(api_key, region="IN", lookback=30, per_query=8, max_queries=12, language="en"):
    cutoff=(datetime.now(timezone.utc)-timedelta(days=lookback)).isoformat().replace("+00:00","Z")
    queries=[]
    for cat, qs in QUERY_PACK.items():
        for q in qs:
            queries.append((cat,q))
    queries=queries[:max_queries]
    raw=[]
    sess=requests.Session()
    for cat,q in queries:
        params={"part":"snippet","q":q,"type":"video","order":"date","publishedAfter":cutoff,"maxResults":min(int(per_query),50),"regionCode":region,"relevanceLanguage":language,"key":api_key}
        r=sess.get("https://www.googleapis.com/youtube/v3/search",params=params,timeout=20)
        r.raise_for_status()
        for item in r.json().get("items",[]):
            vid=item.get("id",{}).get("videoId")
            if not vid: continue
            sn=item.get("snippet",{})
            raw.append({"video_id":vid,"title":sn.get("title",""),"description":sn.get("description",""),"channel":sn.get("channelTitle",""),"published_at":sn.get("publishedAt",""),"thumbnail":sn.get("thumbnails",{}).get("high",{}).get("url") or sn.get("thumbnails",{}).get("medium",{}).get("url"),"query_category":cat})
    unique={x["video_id"]:x for x in raw}
    vids=list(unique.values())
    results=[]
    for i in range(0,len(vids),50):
        ids=",".join(x["video_id"] for x in vids[i:i+50])
        r=sess.get("https://www.googleapis.com/youtube/v3/videos",params={"part":"snippet,statistics","id":ids,"key":api_key},timeout=20)
        r.raise_for_status()
        for item in r.json().get("items",[]):
            base=unique.get(item.get("id"),{})
            stt=item.get("statistics",{})
            pub=base.get("published_at") or item.get("snippet",{}).get("publishedAt")
            try: age=(datetime.now(timezone.utc)-datetime.fromisoformat(pub.replace("Z","+00:00"))).total_seconds()/86400
            except: age=1
            x={**base,"views":int(stt.get("viewCount",0) or 0),"likes":int(stt.get("likeCount",0) or 0),"comments":int(stt.get("commentCount",0) or 0),"age_days":max(age,0.25)}
            results.append(x)
    # group by candidate product name to estimate source/creator saturation
    names={candidate_name(x["title"]).lower() for x in results}
    rows=[]
    for name in names:
        group=[x for x in results if candidate_name(x["title"]).lower()==name]
        if not group: continue
        g=max(group,key=lambda z:z["views"])
        source_count=len(group); creator_count=len({x["channel"] for x in group})
        trend,uniq,use,demo,sat,opp,status=scores_for(g,source_count,creator_count)
        cat=classify(name+" "+g.get("title","")+" "+g.get("description",""))
        purchase=extract_urls(g.get("description",""))
        product_url=purchase[0] if purchase else "https://www.amazon.in/s?k="+quote_plus(name)
        rows.append({"name":name,"category":cat,"segment":"Viral / Trending Products" if status=="Viral/Trending" else "Other Unique & Useful","trend_status":status,"opportunity_score":opp,"trend_score":trend,"uniqueness_score":uniq,"usefulness_score":use,"demo_score":demo,"saturation_score":sat,"why_interesting":f"{source_count} recent YouTube reference video(s) from {creator_count} creator(s); fastest observed video has {g['views']:,} views.","product_url":product_url,"reference_url":"https://www.youtube.com/watch?v="+g["video_id"],"image_url":g.get("thumbnail","") or "","source":"YouTube","channel":g.get("channel",""),"views":g.get("views",0),"likes":g.get("likes",0),"comments":g.get("comments",0),"published_at":g.get("published_at",""),"season":seasonal_tag(name+" "+g.get("title","")),"source_count":source_count,"creator_count":creator_count})
    return pd.DataFrame(rows).sort_values("opportunity_score",ascending=False) if rows else pd.DataFrame()

# Session state
if 'live_df' not in st.session_state: st.session_state.live_df=pd.DataFrame()
if 'last_error' not in st.session_state: st.session_state.last_error=''

st.set_page_config(page_title='Product Hunter', page_icon='🔎', layout='wide', initial_sidebar_state='collapsed')

st.markdown('''
<style>
.block-container{max-width:1400px;padding:1rem 2rem 3rem}
[data-testid="stHeader"]{background:transparent}
.hero{padding:22px 24px;border:1px solid #e7e7e7;border-radius:22px;background:linear-gradient(135deg,#f7f9ff,#ffffff);margin-bottom:18px}
.hero h1{font-size:2.15rem;margin:0 0 5px;font-weight:800;letter-spacing:-.8px}.hero p{margin:0;color:#666}
.section-title{font-size:1.35rem;font-weight:800;margin:20px 0 10px}
.card{height:100%;border:1px solid #e7e7e7;border-radius:18px;background:#fff;overflow:hidden;box-shadow:0 2px 10px rgba(0,0,0,.04)}
.card-img{height:190px;width:100%;object-fit:cover;background:#f3f4f6}.card-body{padding:15px}.badges{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:9px}.badge{font-size:11px;padding:5px 8px;border-radius:999px;background:#f1f3f5;color:#444;font-weight:700}.badge.hot{background:#fff0ed;color:#c0392b}.badge.rising{background:#fff7dc;color:#9a6900}.badge.other{background:#eef5ff;color:#3567a8}
.card-title{font-size:1.06rem;font-weight:800;line-height:1.25;margin:5px 0 7px;color:#171717}.meta{font-size:12px;color:#707070;margin-bottom:9px}.why{font-size:13px;color:#555;line-height:1.45;min-height:54px}.score-row{display:flex;align-items:center;justify-content:space-between;border-top:1px solid #eee;margin-top:12px;padding-top:11px}.score{font-size:1.35rem;font-weight:850}.score small{font-size:10px;color:#777;font-weight:600;display:block}.metrics{font-size:11px;color:#666;line-height:1.6}.links{display:flex;gap:8px;margin-top:13px}.links a{flex:1;text-align:center;text-decoration:none;padding:9px 7px;border-radius:10px;font-size:12px;font-weight:750;border:1px solid #ddd;color:#222;background:#fff}.links a.primary{background:#111;color:#fff;border-color:#111}
.empty{padding:50px 20px;text-align:center;border:1px dashed #ccc;border-radius:18px;color:#666}
@media(max-width:700px){.block-container{padding:.7rem .7rem 2rem}.hero{padding:18px;border-radius:17px}.hero h1{font-size:1.65rem}.card-img{height:165px}.card-title{font-size:1rem}.links a{font-size:11px;padding:8px 4px}}
</style>
''',unsafe_allow_html=True)

with st.sidebar:
    st.header('⚙️ Discovery settings')
    api_key=st.text_input('YouTube API key', type='password', value=st.secrets.get('YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY', '')) if hasattr(st,'secrets') else os.getenv('YOUTUBE_API_KEY',''))
    region=st.selectbox('Region',['IN','US','GB','AE','AU','CA','SG','JP'],index=0)
    lookback=st.slider('Lookback days',1,90,30)
    per_query=st.slider('Videos per query',3,20,8)
    max_queries=st.slider('Queries per run',3,12,8)
    if st.button('🚀 Run live discovery',use_container_width=True):
        if not api_key:
            st.session_state.last_error='Add a YouTube Data API v3 key in Settings first.'
        else:
            with st.spinner('Finding recent product content…'):
                try:
                    st.session_state.live_df=youtube_discover(api_key,region,lookback,per_query,max_queries)
                    st.session_state.last_error=''
                except Exception as e:
                    st.session_state.last_error=f'YouTube discovery failed: {type(e).__name__}: {e}'
    st.divider()
    st.caption('Demo mode works without an API key. Live discovery uses YouTube reference content only; it does not download videos.')

raw=st.session_state.live_df.copy() if not st.session_state.live_df.empty else pd.DataFrame(DEMO)
st.markdown('<div class="hero"><h1>🔎 Product Hunter</h1><p>Discover products people are talking about before your next review.</p></div>',unsafe_allow_html=True)

c1,c2,c3,c4=st.columns([2.4,1.15,1.15,1.15])
with c1: search=st.text_input('Search',placeholder='Search products, gadgets, farming tools…',label_visibility='collapsed')
with c2:
    cats=['All']+sorted(set(raw.category.dropna().tolist())); cat=st.selectbox('Category',cats,label_visibility='collapsed')
with c3: status=st.selectbox('Trend',['All','Viral/Trending','Rising','Other'],label_visibility='collapsed')
with c4: sort=st.selectbox('Sort',['Opportunity','Newest trend','Trend','Uniqueness','Usefulness','Lowest saturation'],label_visibility='collapsed')

st.markdown('<div class="section-title">Explore products</div>',unsafe_allow_html=True)
if st.session_state.last_error: st.error(st.session_state.last_error)

data=raw.copy()
if search: data=data[data.name.astype(str).str.contains(search,case=False,na=False)]
if cat!='All': data=data[data.category==cat]
if status!='All': data=data[data.trend_status==status]
sort_map={'Opportunity':'opportunity_score','Trend':'trend_score','Uniqueness':'uniqueness_score','Usefulness':'usefulness_score','Lowest saturation':'saturation_score'}
if sort=='Newest trend' and 'published_at' in data.columns:
    data['_published']=pd.to_datetime(data['published_at'],errors='coerce',utc=True); data=data.sort_values('_published',ascending=False)
else: data=data.sort_values(sort_map.get(sort,'opportunity_score'),ascending=(sort=='Lowest saturation'))

m1,m2,m3,m4=st.columns(4)
m1.metric('Products found',len(data)); m2.metric('Viral / Trending',int((data.trend_status=='Viral/Trending').sum())); m3.metric('Rising',int((data.trend_status=='Rising').sum())); m4.metric('Avg opportunity',round(data.opportunity_score.mean()) if len(data) else 0)

if st.session_state.live_df.empty: st.info('✨ Demo mode — sample products are shown so you can check the interface. Add your YouTube API key in ⚙️ Settings for live discovery.')
else: st.success(f'Live discovery found {len(st.session_state.live_df)} product candidates.')

if len(data):
    csv=data.to_csv(index=False).encode('utf-8'); st.download_button('⬇️ Export results',csv,'product_hunter_results.csv','text/csv')
    cards=[]
    for _,p in data.iterrows():
        name=html.escape(str(p.get('name','Unknown product'))); catv=html.escape(str(p.get('category',''))); segment=html.escape(str(p.get('segment','')))
        stat=str(p.get('trend_status','Other')); badge_class='hot' if stat=='Viral/Trending' else ('rising' if stat=='Rising' else 'other')
        img=str(p.get('image_url','') or ''); img=img if img else 'https://placehold.co/800x500/f3f4f6/555?text=Product+Preview'; img=html.escape(img,quote=True)
        product_url=html.escape(str(p.get('product_url','') or '#'),quote=True); ref_url=html.escape(str(p.get('reference_url','') or '#'),quote=True)
        why=html.escape(str(p.get('why_interesting','') or 'Useful product candidate with review potential.'))
        opp=int(p.get('opportunity_score',0)); trend=int(p.get('trend_score',0)); uniq=int(p.get('uniqueness_score',0)); use=int(p.get('usefulness_score',0)); sat=int(p.get('saturation_score',0))
        season=html.escape(str(p.get('season','') or '')); season_badge=f'<span class="badge">🌦️ {season}</span>' if season else ''
        card=f'''<div class="card"><img class="card-img" src="{img}" loading="lazy"><div class="card-body"><div class="badges"><span class="badge {badge_class}">{html.escape(stat)}</span><span class="badge">{catv}</span>{season_badge}</div><div class="card-title">{name}</div><div class="meta">{segment}</div><div class="why">{why}</div><div class="score-row"><div class="score">{opp}<small>OPPORTUNITY / 100</small></div><div class="metrics">Trend {trend} · Unique {uniq}<br>Useful {use} · Saturation {sat}</div></div><div class="links"><a class="primary" href="{product_url}" target="_blank">🛒 View product</a><a href="{ref_url}" target="_blank">▶ Reference</a></div></div></div>'''
        cards.append(card)
    for i in range(0,len(cards),3):
        cols=st.columns(3,gap='medium')
        for j,col in enumerate(cols):
            if i+j<len(cards):
                with col: st.markdown(cards[i+j],unsafe_allow_html=True)
else:
    st.markdown('<div class="empty"><div style="font-size:2rem">🔎</div><h3>No products found</h3><p>Try another search, category or trend filter.</p></div>',unsafe_allow_html=True)

st.divider(); st.caption('Product Hunter is a research tool. Social references are used for discovery; videos are not downloaded or republished. Opportunity scores are analytical signals, not guarantees.')
