from fastapi import FastAPI
from app.database import engine, Base

from app.models.user import User
from app.models.content import Content
from app.models.interaction import InteractionEvent

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
def home():
    return {
        "message":
        "Recommendation System API Running"
    }