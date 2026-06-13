from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Content(Base):
    __tablename__ = "content"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    tags = Column(String)
    duration = Column(Integer)
    language = Column(String)
    rating = Column(Float)

    content_type = Column( String, nullable=False)