from sqlalchemy.orm import declarative_base
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)          # "income" or "expense"
    category = Column(String, nullable=False)
    description = Column(String, nullable=True)
    payment_method = Column(String, nullable=True)
    date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)