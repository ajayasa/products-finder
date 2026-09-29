import os
from dotenv import load_dotenv
load_dotenv()
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '').strip()
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/products.db')
