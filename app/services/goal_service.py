from app.database.session import SessionLocal
from app.models.goal import Goal

def add_goal(name, goal_type, target_amount, target_date=None):
    session = SessionLocal()
    try:
        goal = Goal(name=name, goal_type=goal_type, target_amount=target_amount, target_date=target_date)
        session.add(goal)
        session.commit()
        session.refresh(goal)
        return goal
    finally:
        session.close()

def get_all_goals():
    session = SessionLocal()
    try:
        return session.query(Goal).all()
    finally:
        session.close()

def add_contribution(goal_id, amount):
    session = SessionLocal()
    try:
        goal = session.query(Goal).filter(Goal.id == goal_id).first()
        goal.current_amount += amount
        session.commit()
        session.refresh(goal)
        return goal
    finally:
        session.close()

from datetime import datetime

def get_goal_pacing(goal):
    if not goal.target_date:
        return None

    now = datetime.now()
    days_remaining = (goal.target_date - now).days
    amount_remaining = goal.target_amount - goal.current_amount

    if days_remaining <= 0:
        return {"status": "overdue", "amount_remaining": amount_remaining}

    weeks_remaining = max(days_remaining / 7, 1)
    required_weekly = amount_remaining / weeks_remaining

    return {
        "status": "overdue" if amount_remaining > 0 and days_remaining <= 0 else "on_track" if amount_remaining <= 0 else "active",
        "days_remaining": days_remaining,
        "amount_remaining": amount_remaining,
        "required_weekly": required_weekly,
    }