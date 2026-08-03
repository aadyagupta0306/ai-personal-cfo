from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime, timezone
from app.models.transaction import Base

class ExpectedTransaction(Base):
    __tablename__ = "expected_transactions"

    id = Column(Integer, primary_key=True)
    label = Column(String, nullable=False)
    type = Column(String, nullable=False)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    expected_date = Column(DateTime, nullable=False)
    status = Column(String, default="pending")
    is_recurring = Column(String, default="no")
    linked_goal_id = Column(Integer, nullable=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    fulfilled_transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))