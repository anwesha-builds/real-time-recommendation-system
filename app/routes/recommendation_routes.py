from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.recommendation_service import (
    get_recommendations
)

router = APIRouter()


@router.get(
    "/recommendations/{user_id}"
)
def recommend_content(
    user_id: int,
    db: Session = Depends(get_db)
):

    recommendations = (
        get_recommendations(
            user_id,
            db
        )
    )

    return [
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