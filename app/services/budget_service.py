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

from calendar import monthrange
from datetime import datetime

def get_budget_velocity(category, month, budget_amount):
    year, month_num = map(int, month.split("-"))
    days_in_month = monthrange(year, month_num)[1]

    now = datetime.now()
    if now.year == year and now.month == month_num:
        days_elapsed = now.day
    else:
        days_elapsed = days_in_month  # past month, fully elapsed

    spent = get_spent_for_category(category, month)
    daily_rate = spent / days_elapsed if days_elapsed > 0 else 0
    projected_month_end = daily_rate * days_in_month
    days_remaining = days_in_month - days_elapsed
    remaining_budget = budget_amount - spent
    safe_daily_spend = remaining_budget / days_remaining if days_remaining > 0 else 0

    return {
        "spent": spent,
        "daily_rate": daily_rate,
        "projected_month_end": projected_month_end,
        "days_remaining": days_remaining,
        "safe_daily_spend": safe_daily_spend,
        "will_exceed": projected_month_end > budget_amount,
    }