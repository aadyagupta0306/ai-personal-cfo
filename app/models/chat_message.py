from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.models.transaction import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)       # "user" or "assistant"
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))