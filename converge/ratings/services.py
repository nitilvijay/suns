from typing import Dict
from django.db.models import Avg, Count, Sum
from .models import Rating

CATEGORY_WEIGHTS = {
    "technical": 0.30,
    "reliability": 0.25,
    "communication": 0.20,
    "initiative": 0.15,
    "overall": 0.10,
}
PRIOR_MEAN = 3.5
PRIOR_WEIGHT = 3


def calculate_raw_rating(category_scores: Dict[str, float]) -> float:
    total = 0.0
    for cat, score in category_scores.items():
        w = CATEGORY_WEIGHTS.get(cat, 0)
        total += w * float(score)
    return round(total, 3)


def submit_rating_record(rater_id: int, ratee_id: int, project_id: str, category_scores: Dict[str, float]) -> Rating:
    raw = calculate_raw_rating(category_scores)
    adjusted = raw  # placeholder for rater reliability multiplier
    return Rating.objects.create(
        rater_id=rater_id,
        ratee_id=ratee_id,
        project_id=project_id,
        category_scores=category_scores,
        raw_rating=raw,
        adjusted_rating=adjusted,
    )


def get_global_rating_data(ratee_id: int) -> Dict:
    qs = Rating.objects.filter(ratee_id=ratee_id)
    count = qs.count()
    if count == 0:
        return {"global_rating": PRIOR_MEAN, "ratings_count": 0}
    sum_adj = qs.aggregate(total=Sum("adjusted_rating"))['total'] or 0.0
    global_rating = (PRIOR_MEAN * PRIOR_WEIGHT + sum_adj) / (PRIOR_WEIGHT + count)
    return {"global_rating": round(global_rating, 3), "ratings_count": count}
