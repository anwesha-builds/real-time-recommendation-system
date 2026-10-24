import json

from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.redis_client import redis_client
from app.services.recommendation_service import (
    get_recommendations
)

router = APIRouter()

CACHE_TTL_SECONDS = 60


@router.get(
    "/recommendations/{user_id}"
)
def recommend_content(
    user_id: int,
    db: Session = Depends(get_db)
):

    cache_key = f"recommendations:{user_id}"
    cached_result = redis_client.get(cache_key)

    if cached_result:
        return {
            "cached": True,
            "recommendations": json.loads(cached_result)
        }

    recommendations = (
        get_recommendations(
            user_id,
            db
        )
    )

    result = [
        {
            "id": item.id,
            "title": item.title,
            "genre": item.genre,
            "content_type":
                item.content_type,
            "rating": item.rating
        }

        for item
        in recommendations
    ]

    redis_client.setex(
        cache_key,
        CACHE_TTL_SECONDS,
        json.dumps(result)
    )

    return {
        "cached": False,
        "recommendations": result
    }
