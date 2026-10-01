from __future__ import annotations

import re

CATEGORIES = {
    'Unique & Clever': ['clever', 'invention', 'innovative', 'smart product', 'genius'],
    'Problem-Solving': ['problem', 'solution', 'fix', 'organizer', 'space saving', 'leak proof'],
    'Home & Kitchen': ['kitchen', 'cooking', 'home', 'storage', 'food', 'sealer', 'chopper', 'cleaning'],
    'Tech & Gadgets': ['gadget', 'usb', 'bluetooth', 'smart', 'electronic', 'charger', 'phone', 'camera'],
    'Car & Bike': ['car', 'vehicle', 'bike', 'motorcycle', 'scooter', 'tyre', 'tire', 'dashcam'],
    'Travel': ['travel', 'camping', 'luggage', 'airport', 'portable', 'road trip'],
    'Personal Use & Grooming': ['grooming', 'shaver', 'trimmer', 'hair', 'beauty', 'skincare'],
    'Village / Rural': ['village', 'rural', 'desi', 'gaon', 'rural home'],
    'Farming & Agriculture': ['farm', 'farmer', 'farming', 'agriculture', 'soil', 'seed', 'crop', 'sprayer', 'weeder', 'irrigation', 'fertilizer'],
    'Seasonal': ['summer', 'monsoon', 'winter', 'diwali', 'festival', 'sankranti', 'ugadi', 'dussehra', 'christmas'],
    'Outdoor & Garden': ['garden', 'outdoor', 'plant', 'watering', 'camping', 'lawn'],
    'Tools & DIY': ['tool', 'diy', 'drill', 'wrench', 'screwdriver', 'repair'],
    'Cleaning & Organization': ['cleaning', 'organizer', 'storage', 'dust', 'mop', 'vacuum'],
    'Safety & Emergency': ['safety', 'emergency', 'first aid', 'alarm', 'lock', 'reflective'],
    'Kids & Parents': ['kids', 'child', 'baby', 'parent', 'toy'],
    'Elderly / Senior-Friendly': ['elderly', 'senior', 'arthritis', 'walker', 'assist'],
    'Office & Work From Home': ['office', 'desk', 'work from home', 'wfh', 'keyboard', 'mouse'],
    'Money-Saving': ['save money', 'energy saving', 'reusable', 'refill', 'economical'],
    'Local / Indian-Specific': ['india', 'indian', 'masala', 'roti', 'idli', 'rangoli'],
}

SEASONS = {
    'Summer': ['summer', 'heat', 'hot weather', 'cooling'],
    'Monsoon': ['monsoon', 'rain', 'rainy', 'waterproof'],
    'Winter': ['winter', 'cold', 'warm', 'heating'],
    'Sankranti': ['sankranti', 'pongal', 'kite'],
    'Ugadi': ['ugadi'],
    'Dasara / Dussehra': ['dasara', 'dussehra'],
    'Diwali': ['diwali', 'deepavali'],
    'Christmas / New Year': ['christmas', 'new year'],
    'Wedding season': ['wedding', 'marriage', 'bridal'],
    'School / college reopening': ['school', 'college', 'back to school'],
    'Travel season': ['travel season', 'holiday', 'vacation', 'tour'],
}


def classify(text: str) -> tuple[str, list[str]]:
    x = re.sub(r'\s+', ' ', (text or '').lower())
    scores = {name: sum(1 for kw in kws if kw in x) for name, kws in CATEGORIES.items()}
    category = max(scores, key=scores.get) if max(scores.values(), default=0) else 'Unique & Clever'
    seasons = [season for season, kws in SEASONS.items() if any(kw in x for kw in kws)]
    return category, seasons
