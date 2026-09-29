import sqlite3
from pathlib import Path
from .config import DATABASE_PATH

SCHEMA = '''
CREATE TABLE IF NOT EXISTS products (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_key TEXT UNIQUE,
 name TEXT NOT NULL,
 brand TEXT,
 category TEXT,
 segment TEXT,
 description TEXT,
 product_url TEXT,
 image_url TEXT,
 country TEXT,
 price TEXT,
 india_availability TEXT,
 trend_status TEXT,
 trend_score INTEGER,
 uniqueness_score INTEGER,
 usefulness_score INTEGER,
 demo_score INTEGER,
 saturation_score INTEGER,
 india_relevance INTEGER,
 opportunity_score INTEGER,
 why_interesting TEXT,
 created_at TEXT,
 updated_at TEXT
);
CREATE TABLE IF NOT EXISTS sources (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 product_id INTEGER,
 source_type TEXT,
 url TEXT,
 title TEXT,
 channel_or_account TEXT,
 views INTEGER,
 likes INTEGER,
 comments INTEGER,
 published_at TEXT,
 verified INTEGER DEFAULT 0,
 FOREIGN KEY(product_id) REFERENCES products(id)
);
'''

def connect():
    Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DATABASE_PATH)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c

def upsert_product(p):
    c = connect()
    cur = c.cursor()
    cur.execute('''INSERT INTO products(product_key,name,brand,category,segment,description,product_url,image_url,country,price,india_availability,trend_status,trend_score,uniqueness_score,usefulness_score,demo_score,saturation_score,india_relevance,opportunity_score,why_interesting,created_at,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))
    ON CONFLICT(product_key) DO UPDATE SET name=excluded.name, description=excluded.description, product_url=excluded.product_url, image_url=excluded.image_url, trend_status=excluded.trend_status, trend_score=excluded.trend_score, uniqueness_score=excluded.uniqueness_score, usefulness_score=excluded.usefulness_score, demo_score=excluded.demo_score, saturation_score=excluded.saturation_score, opportunity_score=excluded.opportunity_score, updated_at=datetime('now')''',
    (p['product_key'],p['name'],p.get('brand',''),p.get('category','Unique & Clever'),p.get('segment','Other'),p.get('description',''),p.get('product_url',''),p.get('image_url',''),p.get('country',''),p.get('price',''),p.get('india_availability','Unknown'),p.get('trend_status','Other'),p.get('trend_score',0),p.get('uniqueness_score',0),p.get('usefulness_score',0),p.get('demo_score',0),p.get('saturation_score',0),p.get('india_relevance',0),p.get('opportunity_score',0),p.get('why_interesting','')))
    c.commit()
    pid = cur.execute('SELECT id FROM products WHERE product_key=?',(p['product_key'],)).fetchone()[0]
    c.close()
    return pid

def add_source(product_id, s):
    c=connect(); c.execute('INSERT INTO sources(product_id,source_type,url,title,channel_or_account,views,likes,comments,published_at,verified) VALUES(?,?,?,?,?,?,?,?,?,?)', (product_id,s.get('source_type'),s.get('url'),s.get('title'),s.get('channel_or_account'),s.get('views',0),s.get('likes',0),s.get('comments',0),s.get('published_at'),int(s.get('verified',False)))); c.commit(); c.close()
