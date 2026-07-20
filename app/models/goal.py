from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from app.models.transaction import Base

class Goal(Base):
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    goal_type = Column(String, nullable=False)      # "savings", "trip", "purchase", "emergency_fund"
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    target_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))