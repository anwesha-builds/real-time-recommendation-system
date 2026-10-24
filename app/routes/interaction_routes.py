from fastapi import APIRouter

from app.redis_client import redis_client
from app.schemas.interaction_schema import (
    InteractionCreate
)
from app.services.event_consumer import EVENT_QUEUE_KEY

router = APIRouter()


@router.post("/event")
def create_interaction(
    interaction: InteractionCreate
):

    redis_client.rpush(
        EVENT_QUEUE_KEY,
        interaction.model_dump_json()
    )

    return {
        "message":
            "Interaction event queued successfully"
    }
