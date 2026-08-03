from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.models.transaction import Base

class ChatSummary(Base):
    __tablename__ = "chat_summary"

    id = Column(Integer, primary_key=True)
    summary_text = Column(String, nullable=False, default="")
    last_summarized_message_id = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))