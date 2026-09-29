import math
from datetime import datetime, timezone

TREND_WORDS = ['viral', 'trending', 'must have', 'amazon find', 'cool gadget', 'useful gadget', 'smart gadget', 'life hack', 'satisfying', 'genius', 'innovative']
PROBLEM_WORDS = ['problem', 'solve', 'solution', 'hack', 'save time', 'save space', 'easy', 'automatic', 'portable', '2 in 1', '3 in 1', 'multi purpose']

def clamp(x):
    return max(0, min(100, int(round(x))))

def score_candidate(title, description='', views=0, likes=0, comments=0, published_at=None, source_count=1, creator_count=1):
    text = f'{title} {description}'.lower()
    trend_terms = sum(1 for w in TREND_WORDS if w in text)
    problem_terms = sum(1 for w in PROBLEM_WORDS if w in text)
    engagement = math.log10(max(views, 1)) * 9 + math.log10(max(likes, 1)) * 4 + math.log10(max(comments, 1)) * 2
    social_breadth = min(100, source_count * 8 + creator_count * 5)
    trend = clamp(engagement + trend_terms * 4 + social_breadth)
    usefulness = clamp(45 + problem_terms * 7)
    visual = clamp(45 + problem_terms * 5 + (10 if any(x in text for x in ['demo', 'test', 'before', 'after']) else 0))
    uniqueness = clamp(78 - trend_terms * 4 - max(0, creator_count - 5) * 4)
    saturation = clamp(creator_count * 8 + max(0, source_count - 5) * 4)
    india = 65
    opportunity = clamp(0.22*uniqueness + 0.22*usefulness + 0.20*visual + 0.18*trend + 0.10*india + 0.08*(100-saturation))
    if trend >= 75 and saturation < 70:
        status = 'Viral/Trending'
    elif trend >= 50 and saturation < 60:
        status = 'Rising'
    else:
        status = 'Other'
    return {
        'trend_score': trend, 'uniqueness_score': uniqueness, 'usefulness_score': usefulness,
        'demo_score': visual, 'saturation_score': saturation, 'india_relevance': india,
        'opportunity_score': opportunity, 'status': status,
    }
