from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
from app.models.transaction import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    account_type = Column(String, nullable=False)   # "bank", "cash", "wallet"
    opening_balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))