import threading

from fastapi import FastAPI
from app.database import engine, Base

from app.models.user import User
from app.models.content import Content
from app.models.interaction import (
    InteractionEvent
)

from app.routes.interaction_routes import (
    router as interaction_router)
from app.routes.recommendation_routes import (
    router as recommendation_router)
from app.routes.analytics_routes import (
    router as analytics_router)
from app.services.event_consumer import consume_events

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(interaction_router)
app.include_router(recommendation_router)
app.include_router(analytics_router)


@app.on_event("startup")
def start_event_consumer():
    threading.Thread(
        target=consume_events,
        daemon=True
    ).start()

@app.get("/")
def home():
    return {
        "message":
        "Recommendation System API Running"
    }