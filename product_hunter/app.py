import streamlit as st
import pandas as pd
from product_hunter.db import connect
from product_hunter.youtube import search_youtube
from product_hunter.ingest import ingest_youtube
from product_hunter.categories import CATEGORIES

st.set_page_config(page_title='Global Product Hunter', layout='wide')
st.title('🌍 Global Product Hunter')
st.caption('YouTube/Instagram-first product discovery for your review channel')

with st.sidebar:
    st.header('Discovery')
    query=st.text_input('YouTube search topic','viral useful gadgets')
    days=st.slider('Look back (days)',1,90,30)
    region=st.selectbox('YouTube region',['IN','US','GB','AE','AU','CA','SG','JP'])
    max_results=st.slider('Results per search',5,50,25)
    if st.button('🔎 Discover products', use_container_width=True):
        try:
            items=search_youtube(query,days,max_results,region)
            products=ingest_youtube(items)
            st.session_state['last_count']=len(products)
            st.success(f'Added {len(products)} candidates')
        except Exception as e:
            st.error(str(e))
    st.divider()
    st.header('Filters')
    cat=st.selectbox('Category',['All']+list(CATEGORIES.keys()))
    status=st.selectbox('Status',['All','Viral/Trending','Rising','Other'])

c=connect()
q='SELECT * FROM products WHERE 1=1'
params=[]
if cat!='All': q+=' AND category=?'; params.append(cat)
if status!='All': q+=' AND trend_status=?'; params.append(status)
q+=' ORDER BY opportunity_score DESC, updated_at DESC'
df=pd.read_sql_query(q,c,params=params)

m1,m2,m3,m4=st.columns(4)
m1.metric('Products',len(df))
m2.metric('Viral / Trending',int((df.trend_status=='Viral/Trending').sum()) if len(df) else 0)
m3.metric('Rising',int((df.trend_status=='Rising').sum()) if len(df) else 0)
m4.metric('Avg opportunity',round(df.opportunity_score.mean()) if len(df) else 0)

st.subheader('Product candidates')
if df.empty:
    st.info('No products yet. Add a YouTube API key in .env and run a discovery search.')
else:
    show=['name','category','trend_status','opportunity_score','uniqueness_score','usefulness_score','demo_score','saturation_score','product_url','image_url']
    st.dataframe(df[show], use_container_width=True, hide_index=True, column_config={
        'product_url':st.column_config.LinkColumn('Product link'),
        'image_url':st.column_config.ImageColumn('Image')
    })
    st.download_button('⬇️ Export CSV',df.to_csv(index=False).encode('utf-8'),'product_hunter.csv','text/csv')

st.divider()
st.subheader('Your category system')
st.write(', '.join(CATEGORIES.keys()))
st.caption('Reference videos/posts are research sources only. The tool is not designed to download or republish creators’ videos.')
