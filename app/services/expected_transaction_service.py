from app.database.session import SessionLocal
from app.models.expected_transaction import ExpectedTransaction
from datetime import datetime, timedelta

def add_expected_transaction(label, type, category, amount, expected_date, is_recurring="no", linked_goal_id=None):
    session = SessionLocal()
    try:
        item = ExpectedTransaction(
            label=label, type=type, category=category, amount=amount,
            expected_date=expected_date, is_recurring=is_recurring, linked_goal_id=linked_goal_id
        )
        session.add(item)
        session.commit()
        session.refresh(item)
        return item
    finally:
        session.close()

def get_upcoming(days_ahead=30):
    session = SessionLocal()
    try:
        return session.query(ExpectedTransaction).filter(
            ExpectedTransaction.status == "pending",
            ExpectedTransaction.expected_date >= datetime.now(),
        ).order_by(ExpectedTransaction.expected_date).all()
    finally:
        session.close()

def mark_status(item_id, status):
    session = SessionLocal()
    try:
        item = session.query(ExpectedTransaction).filter(ExpectedTransaction.id == item_id).first()
        item.status = status
        session.commit()
        session.refresh(item)
        return item
    finally:
        session.close()

def get_all_expected():
    session = SessionLocal()
    try:
        return session.query(ExpectedTransaction).order_by(ExpectedTransaction.expected_date).all()
    finally:
        session.close()

from datetime import timedelta

def get_projected_impact(days_ahead=30):
    session = SessionLocal()
    try:
        cutoff = datetime.now() + timedelta(days=days_ahead)
        items = session.query(ExpectedTransaction).filter(
            ExpectedTransaction.status == "pending",
            ExpectedTransaction.expected_date <= cutoff,
        ).all()

        expected_income = sum(i.amount for i in items if i.type == "income")
        expected_expense = sum(i.amount for i in items if i.type == "expense")
        return expected_income, expected_expense
    finally:
        session.close()

def get_pending_for_matching():
    session = SessionLocal()
    try:
        items = session.query(ExpectedTransaction).filter(ExpectedTransaction.status == "pending").all()
        return [
            {"id": i.id, "label": i.label, "type": i.type, "category": i.category,
             "amount": i.amount, "expected_date": i.expected_date.strftime("%Y-%m-%d")}
            for i in items
        ]
    finally:
        session.close()

def get_forecast(days_ahead=90):
    session = SessionLocal()
    try:
        cutoff = datetime.now() + timedelta(days=days_ahead)
        items = session.query(ExpectedTransaction).filter(
            ExpectedTransaction.status == "pending",
            ExpectedTransaction.expected_date <= cutoff,
        ).order_by(ExpectedTransaction.expected_date).all()

        return [
            {
                "label": i.label,
                "type": i.type,
                "category": i.category,
                "amount": i.amount,
                "date": i.expected_date,
            }
            for i in items
        ]
    finally:
        session.close()