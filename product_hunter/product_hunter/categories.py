CATEGORIES = {
    'Unique & Clever': ['Viral/Trending', 'Other'],
    'Problem-Solving': ['Viral/Trending', 'Other'],
    'Home & Kitchen': ['Viral/Trending', 'Other'],
    'Tech & Gadgets': ['Viral/Trending', 'Other'],
    'Car & Bike': ['Viral/Trending', 'Other'],
    'Travel': ['Viral/Trending', 'Other'],
    'Personal Use & Grooming': ['Viral/Trending', 'Other'],
    'Village / Rural': ['Viral/Trending', 'Other'],
    'Farming & Agriculture': ['Viral/Trending', 'Other'],
    'Seasonal': ['Viral/Trending', 'Other'],
    'Outdoor & Garden': ['Viral/Trending', 'Other'],
    'Tools & DIY': ['Viral/Trending', 'Other'],
    'Cleaning & Organization': ['Viral/Trending', 'Other'],
    'Safety & Emergency': ['Viral/Trending', 'Other'],
    'Kids & Parents': ['Viral/Trending', 'Other'],
    'Elderly / Senior-Friendly': ['Viral/Trending', 'Other'],
    'Office & Work From Home': ['Viral/Trending', 'Other'],
    'Money-Saving': ['Viral/Trending', 'Other'],
    'Local / Indian-Specific': ['Viral/Trending', 'Other'],
}

CATEGORY_KEYWORDS = {
    'Farming & Agriculture': ['farm', 'farmer', 'farming', 'agriculture', 'soil', 'seed', 'crop', 'sprayer', 'weeder', 'irrigation', 'fertilizer', 'pesticide', 'transplanter'],
    'Village / Rural': ['village', 'rural', 'desi', 'indian village', 'gaon', 'rural home'],
    'Car & Bike': ['car', 'bike', 'motorcycle', 'scooter', 'tyre', 'tire', 'dashcam', 'car accessory', 'helmet'],
    'Travel': ['travel', 'camping', 'luggage', 'airport', 'flight', 'road trip', 'portable', 'travel gadget'],
    'Home & Kitchen': ['kitchen', 'cooking', 'food', 'home', 'cleaning', 'organizer', 'storage', 'chopper', 'cutter', 'sealer', 'dispenser'],
    'Tech & Gadgets': ['gadget', 'smart', 'phone', 'mobile', 'charger', 'usb', 'bluetooth', 'camera', 'electronics', 'keyboard', 'mouse'],
    'Tools & DIY': ['tool', 'diy', 'screwdriver', 'repair', 'drill', 'wrench', 'workshop'],
    'Outdoor & Garden': ['garden', 'gardening', 'outdoor', 'camp', 'plant'],
    'Personal Use & Grooming': ['grooming', 'shaver', 'trimmer', 'nail', 'beauty', 'personal care'],
    'Cleaning & Organization': ['cleaning', 'organizer', 'storage', 'dust', 'vacuum', 'laundry'],
    'Safety & Emergency': ['safety', 'emergency', 'alarm', 'tracker', 'first aid'],
    'Office & Work From Home': ['office', 'desk', 'work from home', 'wfh', 'laptop stand', 'desk gadget'],
    'Kids & Parents': ['kids', 'baby', 'children', 'parent'],
    'Elderly / Senior-Friendly': ['elderly', 'senior', 'old age'],
    'Money-Saving': ['save money', 'saving', 'electricity saver', 'water saver', 'fuel saver'],
    'Seasonal': ['summer', 'monsoon', 'rain', 'winter', 'diwali', 'sankranti', 'ugadi', 'christmas', 'wedding season', 'school reopening'],
}

def classify(text: str) -> str:
    t = (text or '').lower()
    scores = {cat: 0 for cat in CATEGORIES}
    for cat, words in CATEGORY_KEYWORDS.items():
        scores[cat] = sum(1 for w in words if w in t)
    best = max(scores, key=scores.get)
    return best if scores[best] else 'Unique & Clever'
