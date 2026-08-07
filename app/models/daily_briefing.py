from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from app.models.transaction import Base

class DailyBriefing(Base):
    __tablename__ = "daily_briefing"

    id = Column(Integer, primary_key=True)
    briefing_text = Column(String, nullable=False)
    generated_date = Column(String, nullable=False)   # "YYYY-MM-DD"
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))