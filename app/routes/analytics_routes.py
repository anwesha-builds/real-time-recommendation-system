from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.interaction import (
    InteractionEvent
)
from app.models.content import Content

router = APIRouter()


@router.get("/analytics/top-content")
def get_top_content(
    db: Session = Depends(get_db)
):

    # Most Watched

    most_watched = (
        db.query(
            Content.title,
            func.count().label(
                "watch_count"
            )
        )
        .join(
            InteractionEvent,
            InteractionEvent.content_id
            == Content.id
        )
        .filter(
            InteractionEvent.event_type
            == "watch_complete"
        )
        .group_by(Content.title)
        .order_by(
            func.count().desc()
        )
        .limit(5)
        .all()
    )

    # Most Liked

    most_liked = (
        db.query(
            Content.title,
            func.count().label(
                "like_count"
            )
        )
        .join(
            InteractionEvent,
            InteractionEvent.content_id
            == Content.id
        )
        .filter(
            InteractionEvent.event_type
            == "like"
        )
        .group_by(Content.title)
        .order_by(
            func.count().desc()
        )
        .limit(5)
        .all()
    )

    # Skip Rate

    total_events = (
        db.query(
            func.count(
                InteractionEvent.id
            )
        )
        .scalar()
    )
    total_skips = (
        db.query(
            func.count(
                InteractionEvent.id
            )
        )
        .filter(
            InteractionEvent.event_type == "skip"
        )
        .scalar()
    )
    skip_rate = (
        round(
            (
                total_skips
                / total_events
            ) * 100,
            2
        )
        if total_events > 0
        else 0
    )

    return {
        "most_watched": [
            {
                "title": row[0],
                "count": row[1]
            }
            for row in most_watched
        ],

        "most_liked": [
            { "title": row[0], "count": row[1] }
            for row in most_liked
        ],

        "skip_rate":
            f"{skip_rate}%"
    }