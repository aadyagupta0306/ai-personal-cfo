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