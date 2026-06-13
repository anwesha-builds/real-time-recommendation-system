from fastapi import FastAPI
from app.database import engine, Base

from app.models.user import User
from app.models.content import Content
from app.models.interaction import (
    InteractionEvent
)

from app.routes.interaction_routes import (
    router as interaction_router
)

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(interaction_router)


@app.get("/")
def home():
    return {
        "message":
        "Recommendation System API Running"
    }