from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.interaction import (
    InteractionEvent
)
from app.models.content import Content


EVENT_WEIGHTS = {
    "like": 5,
    "watch_complete": 4,
    "play": 2,
    "pause": 1,
    "skip": -3,
    "dislike": -5
}


def get_recommendations(
    user_id: int,
    db: Session
):

    # Step 1:
    # Get user interactions

    interactions = (
        db.query(
            InteractionEvent,
            Content.genre
        )
        .join(
            Content,
            InteractionEvent.content_id
            == Content.id
        )
        .filter(
            InteractionEvent.user_id
            == user_id
        )
        .all()
    )

    
    # Step 2:
    # Calculate genre scores

    genre_scores = {}

    for interaction, genre in interactions:

        score = EVENT_WEIGHTS.get(
            interaction.event_type,
            0
        )

        if genre not in genre_scores:
            genre_scores[genre] = 0

        genre_scores[genre] += score

    # Sort genres by score

    sorted_genres = sorted(
        genre_scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    favorite_genres = [
        genre[0]
        for genre in sorted_genres[:5]
    ]

    # Step 3:
    # Already watched content

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

    
    # Step 4:
    # Fetch candidate content

    recommendations = (
        db.query(Content)
        .filter(
            Content.genre.in_(
                favorite_genres
            )
        )
        .filter(
            ~Content.id.in_(
                watched_content
            )
        )
        .order_by(
            Content.rating.desc()
        )
        .limit(20)
        .all()
    )

    # Step 5:
    # Return top 10

    return recommendations[:10]