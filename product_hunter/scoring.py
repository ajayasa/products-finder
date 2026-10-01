from __future__ import annotations

import re

PROBLEM_WORDS = ['problem', 'solution', 'fix', 'easy', 'portable', 'space saving', 'time saving', 'organize', 'prevent', 'protect']


def usefulness_score(title: str, description: str) -> int:
    text = f'{title} {description}'.lower()
    hits = sum(1 for w in PROBLEM_WORDS if w in text)
    return max(40, min(95, 50 + hits * 7))


def uniqueness_score(title: str, description: str) -> int:
    text = f'{title} {description}'.lower()
    uncommon = ['innovative', 'novel', 'clever', 'multi-purpose', '3-in-1', '4-in-1', 'foldable', 'magnetic', 'rechargeable', 'compact']
    hits = sum(1 for w in uncommon if w in text)
    return max(35, min(96, 48 + hits * 8))


def trend_label_from_evidence(trend_score: float | None, social_count: int = 0) -> str:
    if trend_score is None:
        return 'Unverified'
    if trend_score >= 75:
        return 'Viral / Trending'
    if trend_score >= 50:
        return 'Rising'
    return 'Other'


def opportunity_score(usefulness: int, uniqueness: int, trend_score: float | None) -> int | None:
    if trend_score is None:
        return round((0.55 * usefulness) + (0.45 * uniqueness))
    return round((0.35 * usefulness) + (0.30 * uniqueness) + (0.35 * trend_score))
