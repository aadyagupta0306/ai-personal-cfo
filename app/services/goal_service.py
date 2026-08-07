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

def get_goal_priority_ranking(available_amount):
    goals = get_all_goals()
    active = [g for g in goals if g.current_amount < g.target_amount]

    ranked = []
    for g in active:
        pacing = get_goal_pacing(g)
        if pacing and pacing.get("status") == "active":
            urgency = pacing["required_weekly"]
        elif pacing and pacing.get("status") == "overdue":
            urgency = pacing["amount_remaining"]  # treat overdue as maximally urgent
        else:
            urgency = 0  # no deadline set, lowest urgency

        ranked.append({
            "goal": g,
            "urgency": urgency,
            "amount_remaining": g.target_amount - g.current_amount,
        })

    ranked.sort(key=lambda x: x["urgency"], reverse=True)

    total_urgency = sum(r["urgency"] for r in ranked) or 1
    remaining_pool = available_amount

    for r in ranked:
        share = (r["urgency"] / total_urgency) * available_amount
        suggested = min(share, r["amount_remaining"], remaining_pool)
        r["suggested_allocation"] = round(suggested, -1)
        remaining_pool -= r["suggested_allocation"]

    return ranked