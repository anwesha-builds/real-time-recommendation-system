from sqlalchemy.orm import Session

from app.models.interaction import (
    InteractionEvent
)
from app.models.content import Content
from app.redis_client import redis_client
from app.constants import EVENT_WEIGHTS
from app.services.collaborative_filtering import (
    get_collaborative_scores
)

CF_WEIGHT = 1.0


def combine_genre_scores(historical_scores, session_scores):
    """Pure function (no DB/Redis) so it's easy to unit test."""

    all_genres = set(
        historical_scores.keys()
    ).union(
        session_scores.keys()
    )

    final_scores = {}

    for genre in all_genres:
        historical = historical_scores.get(genre, 0)
        session = session_scores.get(genre, 0)

        final_scores[genre] = (
            historical * 0.6
            +
            session * 0.4
        )

    return final_scores


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
    # Get latest session's live score from Redis
    # (updated in real time by the event consumer instead
    # of being recomputed from Postgres on every request)


    latest_session_id = redis_client.get(
        f"latest_session:{user_id}"
    )

    session_scores = {}

    if latest_session_id:

        raw_scores = redis_client.hgetall(
            f"session_score:{user_id}:{latest_session_id}"
        )

        session_scores = {
            genre: float(score)
            for genre, score in raw_scores.items()
        }


    # Step 3:
    # Combine scores


    final_scores = combine_genre_scores(
        historical_scores,
        session_scores
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
    # Fetch a candidate pool (content-based: genre + rating)


    candidates = (
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
        .limit(30)
        .all()
    )

    # Step 6:
    # Re-rank candidates with a collaborative-filtering signal
    # (how similar each candidate is to content this user already
    # liked, based on other users' interaction patterns)

    cf_scores = get_collaborative_scores(
        db,
        user_id,
        [item.id for item in candidates]
    )

    ranked = sorted(
        candidates,
        key=lambda item: (
            item.rating
            + cf_scores.get(item.id, 0.0) * CF_WEIGHT
        ),
        reverse=True
    )

    return ranked[:10]