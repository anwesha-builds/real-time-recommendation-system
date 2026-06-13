from pydantic import BaseModel
from typing import Literal


class InteractionCreate(BaseModel):
    user_id: int
    content_id: int

    event_type: Literal[
        "play",
        "pause",
        "skip",
        "like",
        "dislike",
        "watch_complete"
    ]

    session_id: str