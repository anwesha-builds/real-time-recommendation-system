from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.interaction import (
    InteractionEvent
)
from app.models.content import Content


def get_recommendations(
    user_id: int,
    db: Session
):

    # Step 1:
    # Find user's favorite genres

    favorite_genres = (
        db.query(
            Content.genre,
            func.count().label("count")
        )
        .join(
            InteractionEvent,
            InteractionEvent.content_id
            == Content.id
        )
        .filter(
            InteractionEvent.user_id
            == user_id
        )
        .group_by(Content.genre)
        .order_by(func.count().desc())
        .limit(5)
        .all()
    )

    genre_names = [
        genre[0]
        for genre in favorite_genres
    ]

    # Step 2:
    # Find content user already watched

    watched_content = (
        db.query(
            InteractionEvent.content_id
        )
        .filter(
            InteractionEvent.user_id
            == user_id
        )
        .subquery()
    )

    # Step 3:
    # Recommend unseen content
    recommendations = (
        db.query(Content)
        .filter(
            Content.genre.in_(
                genre_names
            )
        )
        .filter(
            ~Content.id.in_(
                watched_content
            )
        )
        .limit(10)
        .all()
    )

    return recommendations