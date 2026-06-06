from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    DateTime
)
from app.database import Base
from datetime import datetime


class InteractionEvent(Base):
    __tablename__ = "interaction_events"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    content_id = Column(
        Integer,
        ForeignKey("content.id"),
        nullable=False
    )

    event_type = Column(
        String,
        nullable=False
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow
    )