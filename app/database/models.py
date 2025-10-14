from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from .connection import Base


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    original_text = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    title = Column(String(255), nullable=True)
    topics = Column(JSON, nullable=False)  # List of 3 topics
    sentiment = Column(String(20), nullable=False)  # positive/neutral/negative
    keywords = Column(JSON, nullable=False)  # List of 3 keywords
    confidence_score = Column(Integer, nullable=True)  # 0-100
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
