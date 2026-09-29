import streamlit as st
import pandas as pd

st.set_page_config(page_title="Global Product Hunter", page_icon="🔎", layout="wide")

st.markdown("""<style>
.block-container{padding-top:1.2rem;max-width:1200px}
.product-card{border:1px solid #ddd;border-radius:14px;padding:16px;margin:8px 0;height:100%}
.small{font-size:.85rem;opacity:.75}
.score{font-size:1.35rem;font-weight:700}
@media(max-width:700px){.block-container{padding-left:.8rem;padding-right:.8rem}.product-card{padding:12px}}
</style>""", unsafe_allow_html=True)

DATA=[
 {"name":"Foldable Food Sealer","category":"Home & Kitchen","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":86,"trend_score":72,"uniqueness_score":88,"usefulness_score":91,"demo_score":90,"saturation_score":38,"why_interesting":"Easy before/after demonstration and solves a common food-storage problem.","product_url":"https://www.amazon.in/s?k=mini+food+bag+sealer","reference_url":"https://www.youtube.com/results?search_query=mini+food+bag+sealer"},
 {"name":"Smart Soil Moisture Meter","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":84,"trend_score":68,"uniqueness_score":84,"usefulness_score":92,"demo_score":86,"saturation_score":34,"why_interesting":"Useful for home gardening and farming; readings are easy to demonstrate on video.","product_url":"https://www.amazon.in/s?k=soil+moisture+meter","reference_url":"https://www.youtube.com/results?search_query=soil+moisture+meter"},
 {"name":"Portable Tyre Inflator","category":"Car & Bike","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":79,"trend_score":91,"uniqueness_score":63,"usefulness_score":94,"demo_score":95,"saturation_score":71,"why_interesting":"Strong visual demonstration and clear emergency-use case.","product_url":"https://www.amazon.in/s?k=portable+tyre+inflator","reference_url":"https://www.youtube.com/results?search_query=portable+tyre+inflator"},
 {"name":"Rechargeable Mini Chopper","category":"Home & Kitchen","segment":"Viral / Trending Products","trend_status":"Viral/Trending","opportunity_score":76,"trend_score":94,"uniqueness_score":61,"usefulness_score":89,"demo_score":96,"saturation_score":82,"why_interesting":"Highly demonstrable product, but social content is already crowded.","product_url":"https://www.amazon.in/s?k=rechargeable+mini+chopper","reference_url":"https://www.youtube.com/results?search_query=rechargeable+mini+chopper"},
 {"name":"Hand Weeder Tool","category":"Farming & Agriculture","segment":"Other Unique & Useful","trend_status":"Other","opportunity_score":73,"trend_score":48,"uniqueness_score":87,"usefulness_score":88,"demo_score":84,"saturation_score":22,"why_interesting":"Less saturated and particularly relevant for garden and small-farm users.","product_url":"https://www.amazon.in/s?k=hand+weeder+tool","reference_url":"https://www.youtube.com/results?search_query=hand+weeder+tool"},
 {"name":"Travel Cable Organizer","category":"Travel","segment":"Other Unique & Useful","trend_status":"Rising","opportunity_score":81,"trend_score":70,"uniqueness_score":78,"usefulness_score":87,"demo_score":82,"saturation_score":42,"why_interesting":"Compact travel problem-solver with an easy visual transformation demo.","product_url":"https://www.amazon.in/s?k=travel+cable+organizer","reference_url":"https://www.youtube.com/results?search_query=travel+cable+organizer"},
]

df=pd.DataFrame(DATA)

st.title("🔎 Global Product Hunter")
st.caption("Mobile-friendly demo • Social-first product discovery dashboard")

with st.sidebar:
    st.header("Filters")
    search=st.text_input("Search products","")
    categories=["All"]+sorted(df.category.unique().tolist())
    category=st.selectbox("Category",categories)
    statuses=["All","Viral/Trending","Rising","Other"]
    status=st.selectbox("Trend status",statuses)

filtered=df.copy()
if search: filtered=filtered[filtered.name.str.contains(search,case=False,na=False)]
if category!="All": filtered=filtered[filtered.category==category]
if status!="All": filtered=filtered[filtered.trend_status==status]
filtered=filtered.sort_values("opportunity_score",ascending=False)

c1,c2,c3,c4=st.columns(4)
c1.metric("Products",len(filtered))
c2.metric("Viral / Trending",int((filtered.trend_status=="Viral/Trending").sum()))
c3.metric("Rising",int((filtered.trend_status=="Rising").sum()))
c4.metric("Avg Opportunity",round(filtered.opportunity_score.mean()) if len(filtered) else 0)

st.info("Demo data only. These products are placeholders for testing the interface; they are not final recommendations or verified trend findings.")

for _,p in filtered.iterrows():
    with st.container(border=True):
        left,right=st.columns([3,1])
        with left:
            st.subheader(p.name)
            st.write(f"**{p.category}** • {p.segment} • **{p.trend_status}**")
            st.write(p.why_interesting)
            st.markdown(f"**Opportunity:** {p.opportunity_score}/100  |  **Uniqueness:** {p.uniqueness_score}/100  |  **Usefulness:** {p.usefulness_score}/100  |  **Saturation:** {p.saturation_score}/100")
            st.link_button("🛒 Product reference",p.product_url)
            st.link_button("▶️ Social reference search",p.reference_url)
        with right:
            st.metric("Opportunity",p.opportunity_score)
            st.caption("Demo score")

st.divider()
st.caption("Reference links are for research only. The final system will use permitted social/public-web signals and will not download or republish creators' videos.")
