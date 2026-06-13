from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.interaction import InteractionEvent
from app.schemas.interaction_schema import (
    InteractionCreate
)

router = APIRouter()


@router.post("/event")
def create_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db)
):

    new_event = InteractionEvent(
        user_id=interaction.user_id,
        content_id=interaction.content_id,
        event_type=interaction.event_type,
        session_id=interaction.session_id
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return {
        "message":
            "Interaction event stored successfully",

        "event_id":
            new_event.id
    }