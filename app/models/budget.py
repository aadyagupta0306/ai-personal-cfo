from sqlalchemy import Column, Integer, String, Float
from app.models.transaction import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    month = Column(String, nullable=False)   # format: "2026-07"