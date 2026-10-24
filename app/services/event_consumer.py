import json

from app.database import SessionLocal
from app.redis_client import redis_client
from app.models.interaction import InteractionEvent
from app.models.content import Content
from app.constants import EVENT_WEIGHTS

EVENT_QUEUE_KEY = "event_queue"
SESSION_SCORE_TTL_SECONDS = 3600


def consume_events():
    """Blocking loop: pulls events pushed by POST /event and persists them.

    Runs in its own background thread (started in app/main.py) so event
    ingestion stays fast while the actual DB write + real-time score
    update happen out of the request path.
    """

    while True:
        item = redis_client.blpop(EVENT_QUEUE_KEY, timeout=5)

        if item is None:
            continue

        _, payload = item
        data = json.loads(payload)

        db = SessionLocal()
        try:
            event = InteractionEvent(
                user_id=data["user_id"],
                content_id=data["content_id"],
                event_type=data["event_type"],
                session_id=data["session_id"]
            )

            db.add(event)
            db.commit()
            db.refresh(event)

            _update_realtime_state(db, event)

        finally:
            db.close()


def _update_realtime_state(db, event):

    content = (
        db.query(Content)
        .filter(Content.id == event.content_id)
        .first()
    )

    if content is None:
        return

    weight = EVENT_WEIGHTS.get(event.event_type, 0)

    session_key = (
        f"session_score:{event.user_id}:{event.session_id}"
    )

    redis_client.hincrbyfloat(
        session_key,
        content.genre,
        weight
    )
    redis_client.expire(
        session_key,
        SESSION_SCORE_TTL_SECONDS
    )

    redis_client.set(
        f"latest_session:{event.user_id}",
        event.session_id
    )

    redis_client.delete(
        f"recommendations:{event.user_id}"
    )
