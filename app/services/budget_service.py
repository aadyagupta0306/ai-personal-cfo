from app.database.session import SessionLocal
from app.models.budget import Budget
from app.models.transaction import Transaction
from sqlalchemy import func

def add_budget(category, amount, month):
    session = SessionLocal()
    try:
        existing = session.query(Budget).filter(
            Budget.category == category, Budget.month == month
        ).first()
        if existing:
            existing.amount = amount
            session.commit()
            session.refresh(existing)
            return existing
        budget = Budget(category=category, amount=amount, month=month)
        session.add(budget)
        session.commit()
        session.refresh(budget)
        return budget
    finally:
        session.close()

def get_budgets_for_month(month):
    session = SessionLocal()
    try:
        return session.query(Budget).filter(Budget.month == month).all()
    finally:
        session.close()

def get_spent_for_category(category, month):
    session = SessionLocal()
    try:
        spent = session.query(func.sum(Transaction.amount)).filter(
            Transaction.category == category,
            Transaction.type == "expense",
            func.to_char(Transaction.date, "YYYY-MM") == month,
        ).scalar()
        return spent or 0
    finally:
        session.close()