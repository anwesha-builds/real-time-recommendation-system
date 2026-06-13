from sqlalchemy.orm import Session

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
    # Get historical interactions


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

    historical_scores = {}

    for interaction, genre in interactions:

        score = EVENT_WEIGHTS.get(
            interaction.event_type,
            0
        )

        if genre not in historical_scores:
            historical_scores[genre] = 0

        historical_scores[genre] += score


    # Step 2:
    # Get latest session


    latest_session = (
        db.query(
            InteractionEvent.session_id
        )
        .filter(
            InteractionEvent.user_id
            == user_id
        )
        .order_by(
            InteractionEvent.timestamp.desc()
        )
        .first()
    )

    session_scores = {}

    if latest_session:

        session_interactions = (
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
            .filter(
                InteractionEvent.session_id
                == latest_session[0]
            )
            .all()
        )

        for interaction, genre in (
            session_interactions
        ):

            score = EVENT_WEIGHTS.get(
                interaction.event_type,
                0
            )

            if genre not in session_scores:
                session_scores[genre] = 0

            session_scores[genre] += score


    # Step 3:
    # Combine scores


    final_scores = {}

    all_genres = set(
        historical_scores.keys()
    ).union(
        session_scores.keys()
    )

    for genre in all_genres:

        historical = (
            historical_scores.get(
                genre,
                0
            )
        )

        session = (
            session_scores.get(
                genre,
                0
            )
        )

        final_scores[genre] = (
            historical * 0.6
            +
            session * 0.4
        )

    favorite_genres = sorted(
        final_scores,
        key=final_scores.get,
        reverse=True
    )[:5]


    # Step 4:
    # Remove watched content


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


    # Step 5:
    # Fetch recommendations


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